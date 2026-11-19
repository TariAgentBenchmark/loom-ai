import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import AdminAIModelRouteSettings from "@/components/AdminAIModelRouteSettings";
import { adminGetAIModelRoutes, adminUpdateAIModelRoutes } from "@/lib/api";

jest.mock("@/contexts/AdminAuthContext", () => ({ useAdminAccessToken: () => "admin-token" }));
jest.mock("@/lib/api", () => ({
  adminGetAIModelRoutes: jest.fn(),
  adminUpdateAIModelRoutes: jest.fn(),
}));

const route = {
  routeKey: "prompt_edit.model1.4k", label: "用嘴改图 / 模型1 / 4K", provider: "apyi",
  model: "apyi-4k", readOnly: false,
  providers: [
    { provider: "apyi", label: "Apyi", client: "apyi_gemini", models: ["apyi-4k"], defaultModel: "apyi-4k", configured: true },
    { provider: "krapi", label: "Kr API", client: "krapi_gemini", models: ["T香蕉pro", "T香蕉2-4K"], defaultModel: "T香蕉pro", configured: true },
    { provider: "tuzi", label: "Tuzi", client: "tuzi_gemini", models: ["tuzi-4k"], defaultModel: "tuzi-4k", configured: false },
  ],
};
const fixed = {
  routeKey: "expand_image", label: "扩图", provider: "runninghub", model: "current", readOnly: true,
  providers: [{ provider: "runninghub", label: "RunningHub", client: "runninghub", models: ["current"], defaultModel: "current", configured: true }],
};

beforeEach(() => {
  jest.clearAllMocks();
  (adminGetAIModelRoutes as jest.Mock).mockResolvedValue({ data: { routes: [route, fixed] } });
  (adminUpdateAIModelRoutes as jest.Mock).mockImplementation(async (payload) => ({
    data: { routes: [{ ...route, ...payload.routes[0] }, fixed] },
  }));
});

it("only saves manually configurable routes and blocks missing credentials", async () => {
  render(<AdminAIModelRouteSettings />);
  const provider = await screen.findByRole("combobox", { name: "用嘴改图 / 模型1 / 4K 供应商" });
  expect(screen.getByRole("option", { name: "Tuzi（未配置凭据）" })).toBeDisabled();
  expect(screen.getByRole("combobox", { name: "扩图 供应商" })).toBeDisabled();
  expect(screen.getByRole("combobox", { name: "扩图 模型" })).toBeDisabled();
  expect(screen.getByText("单线路")).toBeInTheDocument();
  fireEvent.change(provider, { target: { value: "krapi" } });
  expect(screen.getByRole("combobox", { name: "用嘴改图 / 模型1 / 4K 模型" })).toHaveValue("T香蕉pro");
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));
  await waitFor(() => expect(adminUpdateAIModelRoutes).toHaveBeenCalledWith({
    routes: [{ routeKey: route.routeKey, provider: "krapi", model: "T香蕉pro" }],
  }, "admin-token"));
  expect(await screen.findByText(/已保存，只影响新建任务/)).toBeInTheDocument();
});

it("shows an explicit error instead of claiming save succeeded", async () => {
  (adminUpdateAIModelRoutes as jest.Mock).mockRejectedValue(new Error("所选线路未配置凭据"));
  render(<AdminAIModelRouteSettings />);
  await screen.findByRole("combobox", { name: "用嘴改图 / 模型1 / 4K 供应商" });
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));
  expect(await screen.findByText("所选线路未配置凭据")).toBeInTheDocument();
});
