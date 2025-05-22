"use client";
import React from "react";
import { useState } from "react";
import { Flex, Input, IconButton } from "@chakra-ui/react";
import { FiSend } from "react-icons/fi";
import { useChatStore } from "../store/chat";

export default function ChatInput() {
  const [value, setValue] = useState("");
  const addMessage = useChatStore((state) => state.addMessage);

  const handleSend = () => {
    if (!value.trim()) return;
    
    // ユーザーメッセージを追加
    addMessage({
      role: "user",
      content: value.trim(),
    });

    // TODO: APIを呼び出して応答を取得
    // 仮の応答を追加
    setTimeout(() => {
      addMessage({
        role: "assistant",
        content: "ご質問ありがとうございます！\n現在、APIの実装中です。\nもうしばらくお待ちください。",
      });
    }, 1000);

    setValue("");
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
        isDisabled={!value.trim()}
      />
    </Flex>
  );
} 