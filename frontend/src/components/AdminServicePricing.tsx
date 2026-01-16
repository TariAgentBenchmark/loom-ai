"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Edit3, RefreshCw, X, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import {
  adminGetServicePrices,
  adminUpdateServicePrice,
  AdminServicePrice,
  AdminServiceVariant,
  adminUpdateServiceVariantPrice,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";
import { formatDateTime } from "../lib/datetime";

interface EditFormState {
  serviceName: string;
  priceCredits: string;
  description: string;
  active: boolean;
  inheritPrice: boolean;
}

const defaultFormState: EditFormState = {
  serviceName: "",
  priceCredits: "",
  description: "",
  active: true,
  inheritPrice: false,
};

type EditingTarget =
  | { kind: "service"; service: AdminServicePrice }
  | { kind: "variant"; service: AdminServicePrice; variant: AdminServiceVariant };

const formatCredits = (value: number) => {
  if (Number.isInteger(value)) {
    return value.toString();
  }
  const formatted = value.toFixed(2).replace(/\.00$/, "");
  return formatted.replace(/(\.\d*[1-9])0$/, "$1");
};

const formatCreditsValue = (value?: number | null) => {
  if (value === null || value === undefined) {
    return "-";
  }
  return formatCredits(value);
};

const buildVariantServiceKey = (serviceKey: string, variantKey: string) =>
  `${serviceKey}_${variantKey}`;

const AdminServicePricing: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [services, setServices] = useState<AdminServicePrice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [editingTarget, setEditingTarget] = useState<EditingTarget | null>(null);
  const [formState, setFormState] = useState<EditFormState>(defaultFormState);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const sortedServices = useMemo(
    () => [...services].sort((a, b) => a.serviceKey.localeCompare(b.serviceKey)),
    [services]
  );

  const fetchServices = useCallback(async () => {
    if (!accessToken) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await adminGetServicePrices(accessToken, true);
      setServices(response.data.services);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取服务价格失败");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  const openEditModal = (service: AdminServicePrice) => {
    setEditingTarget({ kind: "service", service });
    setFormState({
      serviceName: service.serviceName,
      priceCredits: service.priceCredits.toString(),
      description: service.description ?? "",
      active: service.active,
      inheritPrice: false,
    });
    setFormError(null);
  };

  const openVariantEditModal = (service: AdminServicePrice, variant: AdminServiceVariant) => {
    setEditingTarget({ kind: "variant", service, variant });
    setFormState({
      serviceName: variant.variantName,
      priceCredits: variant.inheritsPrice
        ? ""
        : (variant.priceCredits ?? variant.effectivePriceCredits).toString(),
      description: variant.description ?? "",
      active: variant.active,
      inheritPrice: variant.inheritsPrice,
    });
    setFormError(null);
  };

  const closeEditModal = () => {
    setEditingTarget(null);
    setFormState(defaultFormState);
    setFormError(null);
    setIsSubmitting(false);
  };

  const updateFormState = (updates: Partial<EditFormState>) => {
    setFormState((prev) => ({
      ...prev,
      ...updates,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingTarget || !accessToken) {
      return;
    }

    const trimmedName = formState.serviceName.trim();
    if (!trimmedName) {
      setFormError("功能名称不能为空");
      return;
    }

    const isVariant = editingTarget.kind === "variant";
    const inheritPrice = isVariant && formState.inheritPrice;
    let priceValue: number | null = null;
    if (!inheritPrice) {
      priceValue = Number(formState.priceCredits);
      if (!Number.isFinite(priceValue) || priceValue < 0) {
        setFormError("请输入有效的积分价格");
        return;
      }
    }

    setIsSubmitting(true);
    setFormError(null);
    setError(null);
    setSuccessMessage(null);

    try {
      if (editingTarget.kind === "service") {
        const response = await adminUpdateServicePrice(
          editingTarget.service.serviceKey,
          {
            priceCredits: priceValue ?? 0,
            serviceName: trimmedName,
            description: formState.description.trim(),
            active: formState.active,
          },
          accessToken
        );

        const updatedService = response.data.service;
        setServices((prev) =>
          prev.map((item) => {
            if (item.serviceKey !== updatedService.serviceKey) {
              return item;
            }
            const nextVariants =
              updatedService.variants?.length
                ? updatedService.variants
                : item.variants.map((variant) =>
                    variant.inheritsPrice
                      ? { ...variant, effectivePriceCredits: updatedService.priceCredits }
                      : variant
                  );
            return { ...updatedService, variants: nextVariants };
          })
        );
        setSuccessMessage("服务价格已更新");
      } else {
        const response = await adminUpdateServiceVariantPrice(
          editingTarget.service.serviceKey,
          editingTarget.variant.variantKey,
          {
            priceCredits: inheritPrice ? null : priceValue,
            inheritPrice,
            variantName: trimmedName,
            description: formState.description.trim(),
            active: formState.active,
          },
          accessToken
        );

        const updatedVariant = response.data.variant;
        setServices((prev) =>
          prev.map((item) =>
            item.serviceKey === editingTarget.service.serviceKey
              ? {
                  ...item,
                  variants: item.variants.map((variant) =>
                    variant.variantKey === updatedVariant.variantKey
                      ? updatedVariant
                      : variant
                  ),
                }
              : item
          )
        );
        setSuccessMessage("子模式价格已更新");
      }
      closeEditModal();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "更新服务价格失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">功能积分价格管理</h1>
          <p className="mt-1 text-sm text-gray-600">
            查看并调整各功能的积分价格，调整后前端会实时生效。
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchServices}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                刷新中...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                刷新
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                功能
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                标识
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                积分价格
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                状态
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                最近更新
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-gray-500">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedServices.map((service) => (
              <React.Fragment key={service.serviceKey}>
                <tr>
                  <td className="px-4 py-3">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{service.serviceName}</div>
                      <div className="mt-1 text-xs text-gray-500">主功能</div>
                      {service.description && (
                        <div className="mt-1 text-xs text-gray-500 line-clamp-2">{service.description}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    <code className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700">
                      {service.serviceKey}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold text-indigo-600">
                    {formatCredits(service.priceCredits)} 积分
                  </td>
                  <td className="px-4 py-3">
                    {service.active ? (
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                        启用
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                        停用
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {formatDateTime(service.updatedAt ?? service.createdAt)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openEditModal(service)}
                      className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-600 transition hover:border-blue-300 hover:bg-blue-100"
                    >
                      <Edit3 className="h-4 w-4" />
                      编辑
                    </button>
                  </td>
                </tr>
                {service.variants?.map((variant) => (
                  <tr key={buildVariantServiceKey(service.serviceKey, variant.variantKey)} className="bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="pl-6">
                        <div className="text-sm font-medium text-gray-900">{variant.variantName}</div>
                        <div className="mt-1 text-xs text-gray-500">子模式</div>
                        {variant.description && (
                          <div className="mt-1 text-xs text-gray-500 line-clamp-2">{variant.description}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      <code className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700">
                        {buildVariantServiceKey(service.serviceKey, variant.variantKey)}
                      </code>
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold text-indigo-600">
                      <div className="flex items-center gap-2">
                        <span>{formatCreditsValue(variant.effectivePriceCredits)} 积分</span>
                        {variant.inheritsPrice && (
                          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                            继承
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {variant.active ? (
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                          启用
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                          停用
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDateTime(variant.updatedAt ?? variant.createdAt)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openVariantEditModal(service, variant)}
                        className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-600 transition hover:border-blue-300 hover:bg-blue-100"
                      >
                        <Edit3 className="h-4 w-4" />
                        编辑
                      </button>
                    </td>
                  </tr>
                ))}
              </React.Fragment>
            ))}
            {!sortedServices.length && !isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-gray-500">
                  暂无服务价格数据
                </td>
              </tr>
            )}
            {isLoading && !sortedServices.length && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-gray-500">
                  正在加载中...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editingTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30 px-4 py-8">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {editingTarget.kind === "service" ? "调整功能价格" : "调整子模式价格"}
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  {editingTarget.kind === "service"
                    ? `${editingTarget.service.serviceName}（${editingTarget.service.serviceKey}）`
                    : `${editingTarget.service.serviceName} / ${editingTarget.variant.variantName}（${editingTarget.service.serviceKey}_${editingTarget.variant.variantKey}）`}
                </p>
              </div>
              <button
                onClick={closeEditModal}
                className="rounded-full p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
                aria-label="关闭"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  {editingTarget.kind === "service" ? "功能名称" : "子模式名称"}
                </label>
                <input
                  type="text"
                  value={formState.serviceName}
                  onChange={(event) => updateFormState({ serviceName: event.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder={editingTarget.kind === "service" ? "请输入功能名称" : "请输入子模式名称"}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">积分价格</label>
                <div className="relative rounded-lg border border-gray-300 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-200">
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={formState.priceCredits}
                    onChange={(event) => updateFormState({ priceCredits: event.target.value })}
                    disabled={editingTarget.kind === "variant" && formState.inheritPrice}
                    className="w-full rounded-lg px-3 py-2 pr-16 text-sm focus:outline-none disabled:bg-gray-100 disabled:text-gray-400"
                    placeholder={editingTarget.kind === "variant" && formState.inheritPrice ? "继承主功能" : "例如 1.5"}
                  />
                  <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-gray-500">
                    积分/次
                  </span>
                </div>
              </div>

              {editingTarget.kind === "variant" && (
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">继承主功能价格</label>
                  <button
                    type="button"
                    onClick={() => {
                      const nextInherit = !formState.inheritPrice;
                      updateFormState({
                        inheritPrice: nextInherit,
                        priceCredits: nextInherit ? "" : formState.priceCredits,
                      });
                    }}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 transition ${
                      formState.inheritPrice
                        ? "border-blue-500 bg-blue-500"
                        : "border-gray-300 bg-gray-200"
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
                        formState.inheritPrice ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                    <span className="sr-only">切换继承价格</span>
                  </button>
                </div>
              )}

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  {editingTarget.kind === "service" ? "功能描述" : "子模式描述"}
                </label>
                <textarea
                  value={formState.description}
                  onChange={(event) => updateFormState({ description: event.target.value })}
                  className="w-full min-h-[90px] rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="可选：功能说明或调整备注"
                />
              </div>

              <div className="flex items-center justify-between">
                <label htmlFor="service-active" className="text-sm font-medium text-gray-700">
                  是否启用
                </label>
                <button
                  type="button"
                  onClick={() => updateFormState({ active: !formState.active })}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 transition ${
                    formState.active
                      ? "border-blue-500 bg-blue-500"
                      : "border-gray-300 bg-gray-200"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
                      formState.active ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                  <span className="sr-only">切换启用状态</span>
                </button>
              </div>

              {formError && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                  {formError}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeEditModal}
                  className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      保存中...
                    </>
                  ) : (
                    "保存"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminServicePricing;
