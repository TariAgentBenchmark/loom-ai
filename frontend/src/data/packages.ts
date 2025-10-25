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
    credits_per_yuan: pkg.price_yuan > 0 ? pkg.total_credits / pkg.price_yuan : 0,
    is_refundable: isRefundable,
    refund_amount_yuan: refundAmount,
  };
};

const membershipBase: BasePackage[] = [
  {
    package_id: 'membership_3000',
    name: '高性价比会员套餐',
    category: 'membership',
    price_yuan: 3000,
    bonus_credits: 400,
    total_credits: 3400,
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['额外赠送400积分', '畅享全站功能', '积分永不过期', '会员可退款'],
    sort_order: 1,
  },
  {
    package_id: 'membership_6000',
    name: '专业级会员套餐',
    category: 'membership',
    price_yuan: 6000,
    bonus_credits: 900,
    total_credits: 6900,
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['额外赠送900积分', '畅享全站功能', '积分永不过期', '会员可退款'],
    sort_order: 2,
  },
  {
    package_id: 'membership_10000',
    name: '企业级会员套餐',
    category: 'membership',
    price_yuan: 10000,
    bonus_credits: 2000,
    total_credits: 12000,
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['额外赠送2000积分', '畅享全站功能', '积分永不过期', '会员可退款'],
    popular: true,
    recommended: true,
    sort_order: 3,
  },
  {
    package_id: 'membership_15000',
    name: '至尊会员套餐',
    category: 'membership',
    price_yuan: 15000,
    bonus_credits: 3000,
    total_credits: 18000,
    refund_policy: 'refundable',
    refund_deduction_rate: 0.2,
    privileges: ['额外赠送3000积分', '畅享全站功能', '积分永不过期', '会员可退款'],
    sort_order: 4,
  },
];

const discountBase: BasePackage[] = [
  {
    package_id: 'discount_30',
    name: '入门级优惠套餐',
    category: 'discount',
    price_yuan: 30,
    bonus_credits: 0,
    total_credits: 30,
    refund_policy: 'non_refundable',
    refund_deduction_rate: 0,
    privileges: ['畅享全站功能', '积分永不过期', '优惠套餐不可退款'],
    sort_order: 5,
  },
  {
    package_id: 'discount_100',
    name: '标准优惠套餐',
    category: 'discount',
    price_yuan: 100,
    bonus_credits: 10,
    total_credits: 110,
    refund_policy: 'non_refundable',
    refund_deduction_rate: 0,
    privileges: ['额外赠送10积分', '畅享全站功能', '积分永不过期', '优惠套餐不可退款'],
    sort_order: 6,
  },
  {
    package_id: 'discount_300',
    name: '高级优惠套餐',
    category: 'discount',
    price_yuan: 300,
    bonus_credits: 30,
    total_credits: 330,
    refund_policy: 'non_refundable',
    refund_deduction_rate: 0,
    privileges: ['额外赠送30积分', '畅享全站功能', '积分永不过期', '优惠套餐不可退款'],
    popular: true,
    sort_order: 7,
  },
  {
    package_id: 'discount_500',
    name: '专业优惠套餐',
    category: 'discount',
    price_yuan: 500,
    bonus_credits: 50,
    total_credits: 550,
    refund_policy: 'non_refundable',
    refund_deduction_rate: 0,
    privileges: ['额外赠送50积分', '畅享全站功能', '积分永不过期', '优惠套餐不可退款'],
    sort_order: 8,
  },
];

export const membershipPackages: PackageData[] = membershipBase.map((pkg) =>
  withComputedFields(pkg)
);

export const discountPackages: PackageData[] = discountBase.map((pkg) =>
  withComputedFields(pkg)
);
