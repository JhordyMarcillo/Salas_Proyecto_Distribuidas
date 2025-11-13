declare module "sonner" {
  import * as React from "react";

  export type ToastOptions = any;

  export const toast: {
    (opts: any): void;
    success: (opts: any) => void;
    error: (opts: any) => void;
    info: (opts: any) => void;
    warn: (opts: any) => void;
  };

  export const Toaster: React.ComponentType<any>;

  export default {
    toast,
    Toaster,
  };
}
