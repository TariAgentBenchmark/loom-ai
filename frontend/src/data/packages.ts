export type PackageCategory = 'membership' | 'discount';
export type RefundPolicy = 'refundable' | 'non_refundable';

export interface PackageData {
  id: number;
  package_id: string;
  name: string;
  category: PackageCategory;
  price_yuan: number;
  bonus_credits: number;
  total_credits: number;
  gift_label?: string;
  refund_policy: RefundPolicy;
  refund_deduction_rate: number;
  privileges: string[];
  popular?: boolean;
  recommended?: boolean;
  sort_order: number;
  credits_per_yuan: number;
  is_refundable: boolean;
  refund_amount_yuan: number;
}

type BasePackage = Omit<
  PackageData,
  'id' | 'credits_per_yuan' | 'is_refundable' | 'refund_amount_yuan'
>;

const withComputedFields = (pkg: BasePackage, indexOffset = 0): PackageData => {
  const isRefundable = pkg.refund_policy === 'refundable';
  const refundAmount = isRefundable
    ? pkg.price_yuan * (1 - pkg.refund_deduction_rate)
    : 0;
  return {
    ...pkg,
    id: pkg.sort_order + indexOffset,
    gift_label: (pkg as any).gift_label,
    credits_per_yuan: pkg.price_yuan > 0 ? pkg.total_credits / pkg.price_yuan : 0,
    is_refundable: isRefundable,
    refund_amount_yuan: refundAmount,
  };
};

const membershipBase: BasePackage[] = [
  {
    package_id: 'membership_168',
    name: '优惠 套餐',
    category: 'membership',
    price_yuan: 168,
    bonus_credits: 30,
    total_credits: 198,
    gift_label: '到手198分 送约15%',
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['提取约0.33一张图', '积分永不过期', '支持多台电脑登录同一账号', '畅享全站功能', '会员套餐可联系客服退款（赠送不退）'],
    sort_order: 1,
  },
  {
    package_id: 'membership_688',
    name: '专业 套餐',
    category: 'membership',
    price_yuan: 688,
    bonus_credits: 240,
    total_credits: 928,
    gift_label: '到手928分 送约35%',
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['提取约0.29一张图', '畅享全站功能', '积分永不过期', '支持多台电脑登录同一账号', '会员套餐可联系客服退款（赠送不退）'],
    sort_order: 2,
  },
  {
    package_id: 'membership_1888',
    name: '公司 套餐',
    category: 'membership',
    price_yuan: 1888,
    bonus_credits: 1088,
    total_credits: 2976,
    gift_label: '到手2976分 送约58%',
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['提取约0.23一张图', '畅享全站功能', '积分永不过期', '支持多台电脑登录同一账号', '会员套餐可联系客服退款（赠送不退）'],
    popular: true,
    recommended: true,
    sort_order: 3,
  },
  {
    package_id: 'membership_5888',
    name: '商业 套餐',
    category: 'membership',
    price_yuan: 5888,
    bonus_credits: 6000,
    total_credits: 11888,
    gift_label: '到手11888分 送约100%',
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['提取约0.18一张图', '畅享全站功能', '积分永不过期', '支持多台电脑登录同一账号', '提供开具增值税发票', '会员套餐可联系客服退款（赠送不退）'],
    sort_order: 4,
  },
];

const discountBase: BasePackage[] = [
  {
    package_id: 'discount_66',
    name: '试用 套餐',
    category: 'discount',
    price_yuan: 66,
    bonus_credits: 6,
    total_credits: 72,
    gift_label: '到手72分 送约8%',
    refund_policy: 'non_refundable',
    refund_deduction_rate: 0,
    privileges: ['提取约0.38一张图', '积分永不过期', '优惠套餐不可退款'],
    sort_order: 5,
  },
];

export const membershipPackages: PackageData[] = membershipBase.map((pkg) =>
  withComputedFields(pkg)
);

export const discountPackages: PackageData[] = discountBase.map((pkg) =>
  withComputedFields(pkg)
);
