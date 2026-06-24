import type { Messages } from "./types";

declare module "next-intl" {
  interface IntlMessages extends Messages {}
}
