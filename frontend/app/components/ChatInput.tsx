"use client";
import React from "react";
import { useState } from "react";
import { Flex, Input, IconButton } from "@chakra-ui/react";
import { FiSend } from "react-icons/fi";
import { useChatStore } from "../store/chat";

export default function ChatInput() {
  const [value, setValue] = useState("");
  const addMessage = useChatStore((state) => state.addMessage);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!value.trim() || loading) return;

    const message = value.trim();
    addMessage({ role: "user", content: message });
    setValue("");
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message }),
      });
      const data = await res.json();
      addMessage({ role: "assistant", content: data.answer });
    } catch (e) {
      addMessage({ role: "assistant", content: "エラーが発生しました" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex as="form" onSubmit={e => { e.preventDefault(); handleSend(); }} gap={2}>
      <Input
        placeholder="質問を入力してね！"
        value={value}
        onChange={e => setValue(e.target.value)}
        bg="whiteAlpha.800"
        color="black"
        _placeholder={{ color: "gray.500" }}
        size="lg"
        borderRadius="full"
        autoFocus
      />
      <IconButton
        aria-label="送信"
        icon={<FiSend />}
        colorScheme="pink"
        size="lg"
        borderRadius="full"
        type="submit"
        isDisabled={!value.trim() || loading}
      />
    </Flex>
  );
} 