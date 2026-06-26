import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Markdown } from "./Markdown";

describe("Markdown", () => {
  it("renders markdown and preserves Arabic / Unicode", () => {
    render(<Markdown># الجليس الصالح — *perfume seller*</Markdown>);
    expect(screen.getByText(/الجليس الصالح/)).toBeInTheDocument();
  });

  it("does not render dangerous raw HTML (no script/img-onerror injection)", () => {
    const { container } = render(
      <Markdown>{`Hello <img src=x onerror="alert(1)"> <script>alert(2)</script> world`}</Markdown>,
    );
    // raw HTML is not parsed (no rehype-raw) and rehype-sanitize strips anything dangerous.
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    expect(container.innerHTML).not.toContain("onerror");
  });
});
