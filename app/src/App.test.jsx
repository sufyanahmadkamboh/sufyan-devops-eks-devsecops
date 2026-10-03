import { cleanup, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App.jsx";
import { profile } from "./profile.js";

afterEach(cleanup);

describe("profile card", () => {
  it("shows the name and role", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: profile.name })).toBeInTheDocument();
    expect(screen.getByText(profile.role)).toBeInTheDocument();
  });

  it("lists every skill", () => {
    render(<App />);
    const skills = screen.getByRole("list", { name: "Skills" });
    expect(skills.querySelectorAll("li")).toHaveLength(profile.tags.length);
  });

  it("opens external links safely in a new tab", () => {
    render(<App />);
    const portfolio = screen.getByRole("link", { name: "Portfolio" });
    expect(portfolio).toHaveAttribute("target", "_blank");
    expect(portfolio).toHaveAttribute("rel", "noreferrer noopener");
  });

  it("does not open mailto links in a new tab", () => {
    render(<App />);
    expect(screen.getByRole("link", { name: "Contact" })).not.toHaveAttribute("target");
  });

  it("shows which build is running", () => {
    render(<App />);
    expect(screen.getByText(/served from Amazon EKS/)).toBeInTheDocument();
  });
});
