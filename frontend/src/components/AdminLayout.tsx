"use client";

import React, { useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAdminAuth, useAdminUser } from "../contexts/AdminAuthContext";
import {
  Home,
  Users,
  CreditCard,
  ShoppingBag,
  RefreshCw,
  BarChart3,
  LogOut,
  Menu,
  X,
  Gauge,
  KeyRound,
} from "lucide-react";

interface AdminLayoutProps {
  children: ReactNode;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  current: boolean;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const router = useRouter();
  const pathname = usePathname();
  const { logout } = useAdminAuth();
  const adminUser = useAdminUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation: NavItem[] = [
    {
      name: "仪表板",
      href: "/admin/dashboard",
      icon: Home,
      current: pathname === "/admin/dashboard",
    },
    {
      name: "用户管理",
      href: "/admin/users",
      icon: Users,
      current: pathname === "/admin/users" || pathname.startsWith("/admin/users/"),
    },
    {
      name: "订单管理",
      href: "/admin/orders",
      icon: ShoppingBag,
      current: pathname === "/admin/orders" || pathname.startsWith("/admin/orders/"),
    },
    {
      name: "功能价格",
      href: "/admin/services",
      icon: CreditCard,
      current: pathname === "/admin/services" || pathname.startsWith("/admin/services/"),
    },
    {
      name: "统计分析",
      href: "/admin/analytics",
      icon: BarChart3,
      current: pathname === "/admin/analytics",
    },
    {
      name: "渠道 / 邀请码",
      href: "/admin/agents",
      icon: KeyRound,
      current: pathname === "/admin/agents",
    },
    {
      name: "并发监控",
      href: "/admin/limits",
      icon: Gauge,
      current: pathname === "/admin/limits",
    },
  ];

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-40 md:hidden ${sidebarOpen ? "" : "pointer-events-none"}`}>
        <div className={`absolute inset-0 bg-gray-600 transition-opacity ${sidebarOpen ? "opacity-75" : "opacity-0"}`}
             onClick={() => setSidebarOpen(false)} />
        
        <div className={`relative flex w-64 flex-1 flex-col bg-white transform transition-transform ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
          <div className="flex items-center justify-between px-4 py-6 border-b">
            <h1 className="text-xl font-semibold text-gray-900">图云管理后台</h1>
            <button
              type="button"
              className="text-gray-400 hover:text-gray-600"
              aria-label="close"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => {
                  router.push(item.href);
                  setSidebarOpen(false);
                }}
                className={`group flex w-full items-center px-2 py-2 text-sm font-medium rounded-md ${
                  item.current
                    ? "bg-blue-100 text-blue-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <item.icon
                  className={`mr-3 h-5 w-5 flex-shrink-0 ${
                    item.current ? "text-blue-500" : "text-gray-400 group-hover:text-gray-500"
                  }`}
                />
                {item.name}
              </button>
            ))}
          </nav>
          
          <div className="border-t p-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {adminUser?.user.nickname?.charAt(0) || adminUser?.user.email?.charAt(0) || "A"}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">{adminUser?.user.nickname || "管理员"}</p>
                <p className="text-xs text-gray-500">{adminUser?.user.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
            >
              <LogOut className="mr-3 h-5 w-5 text-gray-400" />
              退出登录
            </button>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:fixed md:inset-y-0 md:flex md:w-64 md:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200 overflow-y-auto">
          <div className="flex items-center px-4 py-6 border-b">
            <h1 className="text-xl font-semibold text-gray-900">图云管理后台</h1>
          </div>
          
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => router.push(item.href)}
                className={`group flex w-full items-center px-2 py-2 text-sm font-medium rounded-md ${
                  item.current
                    ? "bg-blue-100 text-blue-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <item.icon
                  className={`mr-3 h-5 w-5 flex-shrink-0 ${
                    item.current ? "text-blue-500" : "text-gray-400 group-hover:text-gray-500"
                  }`}
                />
                {item.name}
              </button>
            ))}
          </nav>
          
          <div className="border-t p-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {adminUser?.user.nickname?.charAt(0) || adminUser?.user.email?.charAt(0) || "A"}
                  </span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">{adminUser?.user.nickname || "管理员"}</p>
                <p className="text-xs text-gray-500">{adminUser?.user.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
            >
              <LogOut className="mr-3 h-5 w-5 text-gray-400" />
              退出登录
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64">
        <div className="flex flex-col flex-1">
          <div className="md:hidden">
            <div className="flex items-center justify-between bg-white px-4 py-2 border-b">
              <button
                type="button"
                className="text-gray-500 hover:text-gray-600"
                aria-label="menu"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="h-6 w-6" />
              </button>
              <h1 className="text-lg font-medium text-gray-900">图云 管理后台</h1>
              <div className="w-6"></div>
            </div>
          </div>
          
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
