import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import PromptEditModelSelector from "@/components/PromptEditModelSelector";
import { PromptEditMode, toPromptEditModel, resolvePricingServiceKey } from "@/lib/processing";

function Wrapper() {
  const [mode, setMode] = useState<PromptEditMode>("pro_4k");
  return <PromptEditModelSelector value={mode} onChange={setMode} />;
}

it("keeps legacy 2K/4K and selects the new 2K provider separately", () => {
  render(<Wrapper />);
  expect(screen.getByRole("button", {name:"模型1"})).toHaveAttribute("aria-pressed","true");
  expect(screen.getByRole("button", {name:"4K"})).toHaveAttribute("aria-pressed","true");
  fireEvent.click(screen.getByRole("button", {name:"模型pro"}));
  expect(screen.queryByRole("button", {name:"4K"})).not.toBeInTheDocument();
  expect(screen.getByText(/当前实测输出2K/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name:"模型1"}));
  expect(screen.getByRole("button", {name:"4K"})).toHaveAttribute("aria-pressed","true");
  fireEvent.click(screen.getByRole("button", {name:"2K"}));
  expect(screen.getByRole("button", {name:"2K"})).toHaveAttribute("aria-pressed","true");
});

it("uses ordinary prompt-edit pricing for Seedream and keeps old 4K pricing", () => {
  expect(toPromptEditModel("seedream_pro")).toBe("seedream_pro");
  expect(toPromptEditModel("standard")).toBe("new");
  expect(toPromptEditModel("pro_4k")).toBe("pro_4k");
  expect(resolvePricingServiceKey("prompt_edit",{promptEditMode:"seedream_pro"})).toBe("prompt_edit");
  expect(resolvePricingServiceKey("prompt_edit",{promptEditMode:"pro_4k"})).toBe("prompt_edit_pro_4k");
});
