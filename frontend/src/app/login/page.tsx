import { redirect } from "next/navigation";

type LoginPageProps = {
  searchParams?: { invite?: string; ref?: string };
};

export default function LoginPage({ searchParams }: LoginPageProps) {
  const invite = searchParams?.invite?.trim();
  const referral = searchParams?.ref?.trim();
  const target = invite
    ? `/?invite=${encodeURIComponent(invite)}`
    : referral
      ? `/?ref=${encodeURIComponent(referral)}`
      : "/";
  redirect(target);
}
