import { redirect } from "next/navigation";

type LoginPageProps = {
  searchParams?: { invite?: string };
};

export default function LoginPage({ searchParams }: LoginPageProps) {
  const invite = searchParams?.invite?.trim();
  const target = invite ? `/?invite=${encodeURIComponent(invite)}` : "/";
  redirect(target);
}
