import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Mock supabase BEFORE importing anything that depends on it
vi.mock("../src/supabase", () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
    },
  },
}));

import { LoginPage } from "../src/components";
import { supabase } from "../src/supabase";

const mockSignIn = vi.mocked(supabase.auth.signInWithPassword);
const mockSignUp = vi.mocked(supabase.auth.signUp);

beforeEach(() => {
  vi.clearAllMocks();
});

// ── rendering ─────────────────────────────────────────────────────────────────

describe("LoginPage rendering", () => {
  it("renders the WarmPath logo", () => {
    render(<LoginPage />);
    expect(screen.getByText("WarmPath")).toBeInTheDocument();
  });

  it("defaults to sign in mode", () => {
    render(<LoginPage />);
    expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
  });

  it("renders email and password inputs", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("renders Sign In and Sign Up tabs", () => {
    render(<LoginPage />);
    // Tab buttons (not the submit button) — use getAllByRole since "Sign In" appears as tab + submit
    const signInButtons = screen.getAllByRole("button", { name: "Sign In" });
    expect(signInButtons.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: "Sign Up" })).toBeInTheDocument();
  });

  it("submit button is disabled when fields are empty", () => {
    render(<LoginPage />);
    const submitBtn = screen.getAllByRole("button").find(
      (b) => b.getAttribute("type") === "submit"
    );
    expect(submitBtn).toBeDisabled();
  });
});

// ── mode switching ────────────────────────────────────────────────────────────

describe("LoginPage mode switching", () => {
  it("switches to sign up mode when Sign Up tab clicked", async () => {
    render(<LoginPage />);
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));
    expect(screen.getByText("Create your account")).toBeInTheDocument();
  });

  it("submit button text changes to Create Account in sign up mode", async () => {
    render(<LoginPage />);
    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));
    const submitBtn = screen.getAllByRole("button").find(
      (b) => b.getAttribute("type") === "submit"
    );
    expect(submitBtn).toHaveTextContent("Create Account");
  });

  it("clears error when switching modes", async () => {
    mockSignIn.mockResolvedValueOnce({ error: new Error("Bad credentials") } as any);
    render(<LoginPage />);

    await userEvent.type(screen.getByLabelText("Email"), "user@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrongpass");
    await userEvent.click(
      screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")!
    );

    await waitFor(() =>
      expect(screen.getByText(/Bad credentials/i)).toBeInTheDocument()
    );

    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));
    expect(screen.queryByText(/Bad credentials/i)).not.toBeInTheDocument();
  });
});

// ── sign in flow ──────────────────────────────────────────────────────────────

describe("LoginPage sign in", () => {
  it("calls signInWithPassword with email and password", async () => {
    mockSignIn.mockResolvedValueOnce({
      data: { session: null, user: null },
      error: null,
    } as any);
    render(<LoginPage />);

    await userEvent.type(screen.getByLabelText("Email"), "user@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(
      screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")!
    );

    expect(mockSignIn).toHaveBeenCalledWith({
      email: "user@test.com",
      password: "password123",
    });
  });

  it("shows error message on failed sign in", async () => {
    mockSignIn.mockResolvedValueOnce({
      error: new Error("Invalid login credentials"),
    } as any);
    render(<LoginPage />);

    await userEvent.type(screen.getByLabelText("Email"), "user@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrongpass");
    await userEvent.click(
      screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")!
    );

    await waitFor(() =>
      expect(screen.getByText(/Invalid login credentials/i)).toBeInTheDocument()
    );
  });
});

// ── sign up flow ──────────────────────────────────────────────────────────────

describe("LoginPage sign up", () => {
  it("calls signUp with email and password", async () => {
    mockSignUp.mockResolvedValueOnce({
      data: { session: null, user: null },
      error: null,
    } as any);
    render(<LoginPage />);

    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));
    await userEvent.type(screen.getByLabelText("Email"), "new@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "newpassword");
    await userEvent.click(
      screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")!
    );

    expect(mockSignUp).toHaveBeenCalledWith({
      email: "new@test.com",
      password: "newpassword",
    });
  });

  it("shows confirmation message after successful sign up", async () => {
    mockSignUp.mockResolvedValueOnce({
      data: { session: null, user: null },
      error: null,
    } as any);
    render(<LoginPage />);

    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));
    await userEvent.type(screen.getByLabelText("Email"), "new@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "newpassword");
    await userEvent.click(
      screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")!
    );

    await waitFor(() =>
      expect(screen.getByText(/Check your email/i)).toBeInTheDocument()
    );
  });

  it("shows error on failed sign up", async () => {
    mockSignUp.mockResolvedValueOnce({
      error: new Error("Email already registered"),
    } as any);
    render(<LoginPage />);

    await userEvent.click(screen.getByRole("button", { name: "Sign Up" }));
    await userEvent.type(screen.getByLabelText("Email"), "existing@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    await userEvent.click(
      screen.getAllByRole("button").find((b) => b.getAttribute("type") === "submit")!
    );

    await waitFor(() =>
      expect(screen.getByText(/Email already registered/i)).toBeInTheDocument()
    );
  });
});
