"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Save,
  Settings2,
} from "lucide-react";
import {
  AIModelRoute,
  adminGetAIModelRoutes,
  adminUpdateAIModelRoutes,
} from "../lib/api";
import { useAdminAccessToken } from "../contexts/AdminAuthContext";

const AdminAIModelRouteSettings: React.FC = () => {
  const accessToken = useAdminAccessToken();
  const [routes, setRoutes] = useState<AIModelRoute[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadRoutes = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      const response = await adminGetAIModelRoutes(accessToken);
      setRoutes(response.data.routes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取AI模型路由配置失败");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    void loadRoutes();
  }, [loadRoutes]);

  const updateRouteProvider = (routeKey: string, provider: string) => {
    setRoutes((currentRoutes) =>
      currentRoutes.map((route) => {
        if (route.routeKey !== routeKey) {
          return route;
        }
        const providerOption = route.providers.find(
          (option) => option.provider === provider,
        );
        return {
          ...route,
          provider,
          model:
            providerOption?.defaultModel ??
            providerOption?.models[0] ??
            route.model,
        };
      }),
    );
  };

  const updateRouteModel = (routeKey: string, model: string) => {
    setRoutes((currentRoutes) =>
      currentRoutes.map((route) =>
        route.routeKey === routeKey ? { ...route, model } : route,
      ),
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      setSuccessMessage(null);
      const response = await adminUpdateAIModelRoutes(
        {
          routes: routes.map((route) => ({
            routeKey: route.routeKey,
            provider: route.provider,
            model: route.model,
          })),
        },
        accessToken,
      );
      setRoutes(response.data.routes);
      setSuccessMessage("AI模型路由配置已保存，只影响新建任务");
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存AI模型路由配置失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Settings2 className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">AI模型路由配置</h2>
          </div>
          <p className="mt-1 text-sm text-gray-600">
            配置后端模型调用的服务商和模型名。配置会在任务创建时写入快照，只影响新建任务。
          </p>
        </div>
        <button
          onClick={() => void loadRoutes()}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          刷新
        </button>
      </div>

      {error && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        {routes.length === 0 && (
          <div className="rounded-lg border border-dashed border-gray-200 px-4 py-6 text-center text-sm text-gray-500">
            {isLoading ? "正在加载模型路由配置..." : "暂无可配置的模型路由"}
          </div>
        )}

        {routes.map((route) => {
          const currentProvider = route.providers.find(
            (option) => option.provider === route.provider,
          );
          const modelOptions = currentProvider?.models ?? [route.model];

          return (
            <div
              key={route.routeKey}
              className="rounded-xl border border-gray-200 bg-gray-50 p-4"
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">
                    {route.label}
                  </h3>
                  <p className="mt-1 text-xs text-gray-500">{route.routeKey}</p>
                  {route.description && (
                    <p className="mt-2 text-sm text-gray-600">{route.description}</p>
                  )}
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[420px]">
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-gray-700">
                      Provider
                    </span>
                    <select
                      value={route.provider}
                      onChange={(event) =>
                        updateRouteProvider(route.routeKey, event.target.value)
                      }
                      className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                    >
                      {route.providers.map((option) => (
                        <option key={option.provider} value={option.provider}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-gray-700">
                      Model
                    </span>
                    <select
                      value={route.model}
                      onChange={(event) =>
                        updateRouteModel(route.routeKey, event.target.value)
                      }
                      className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                    >
                      {modelOptions.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
              {currentProvider?.description && (
                <p className="mt-3 text-sm text-gray-600">
                  {currentProvider.description}
                </p>
              )}
            </div>
          );
        })}

        <div className="flex items-center justify-end">
          <button
            type="submit"
            disabled={isSubmitting || isLoading || routes.length === 0}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            保存配置
          </button>
        </div>
      </form>
    </div>
  );
};

export default AdminAIModelRouteSettings;
