import en from "@/messages/en.json" with { type: "json" };

type MessageShape<T> = T extends string
  ? string
  : T extends number
    ? number
    : T extends boolean
      ? boolean
      : T extends Array<infer U>
        ? Array<MessageShape<U>>
        : { [K in keyof T]: MessageShape<T[K]> };

export type Messages = MessageShape<typeof en>;

export type MessageNamespace = keyof Messages;
