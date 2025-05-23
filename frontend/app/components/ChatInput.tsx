"use client";
import React from "react";
import { useState, useRef, useCallback, useEffect } from "react";
import { 
  Flex, 
  Input, 
  IconButton, 
  useToast,
  Spinner,
  Text,
  Box
} from "@chakra-ui/react";
import { FiSend } from "react-icons/fi";
import { useChatStore } from "../store/chat";

// 環境変数にフォールバックを設定
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChatInput() {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addMessage, sessionId, initializeSession } = useChatStore();
  const toast = useToast();

  // コンポーネントマウント時にセッションを初期化
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  const showErrorToast = useCallback((message: string) => {
    toast({
      title: "エラー",
      description: message,
      status: "error",
      duration: 5000,
      isClosable: true,
      position: "top",
    });
  }, [toast]);

  const handleSend = useCallback(async () => {
    const message = value.trim();
    if (!message || loading) return;

    // バリデーション
    if (message.length > 1000) {
      showErrorToast("メッセージが長すぎます。1000文字以内で入力してください。");
      return;
    }

    // メッセージを追加してUIを更新
    addMessage({ role: "user", content: message });
    setValue("");
    setLoading(true);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒タイムアウト

      // session_idを含むリクエストボディを作成
      const requestBody = {
        query: message,
        session_id: sessionId
      };

      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      
      if (data.answer) {
        addMessage({ role: "assistant", content: data.answer });
      } else {
        throw new Error("AIからの応答が正常ではありません");
      }

    } catch (error) {
      console.error("Chat API error:", error);
      
      let errorMessage = "申し訳ございません。エラーが発生しました。";
      
      if (error instanceof Error) {
        if (error.name === "AbortError") {
          errorMessage = "リクエストがタイムアウトしました。もう一度お試しください。";
        } else if (error.message.includes("Failed to fetch")) {
          errorMessage = "サーバーに接続できません。ネットワーク接続を確認してください。";
        }
      }
      
      addMessage({ role: "assistant", content: errorMessage });
      showErrorToast(errorMessage);
    } finally {
      setLoading(false);
      // フォーカスを戻す
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [value, loading, addMessage, showErrorToast, sessionId]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const isDisabled = !value.trim() || loading;

  return (
    <Box>
      <Flex 
        as="form" 
        onSubmit={(e) => { 
          e.preventDefault(); 
          handleSend(); 
        }} 
        gap={3}
        align="center"
      >
        <Input
          ref={inputRef}
          placeholder="質問を入力してね！（例：兼六園について教えて）"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyPress={handleKeyPress}
          bg="whiteAlpha.900"
          color="gray.800"
          _placeholder={{ color: "gray.500" }}
          size="lg"
          borderRadius="full"
          border="2px solid"
          borderColor="whiteAlpha.300"
          _hover={{ borderColor: "pink.300" }}
          _focus={{ 
            borderColor: "pink.400",
            boxShadow: "0 0 0 1px #ED64A6"
          }}
          autoFocus
          disabled={loading}
          maxLength={1000}
        />
        <IconButton
          aria-label={loading ? "送信中..." : "メッセージを送信"}
          icon={loading ? <Spinner size="sm" /> : <FiSend />}
          colorScheme="pink"
          size="lg"
          borderRadius="full"
          type="submit"
          isDisabled={isDisabled}
          _hover={{ 
            transform: isDisabled ? "none" : "scale(1.05)",
            transition: "transform 0.2s"
          }}
        />
      </Flex>
      
      {/* 文字数表示 */}
      {value.length > 800 && (
        <Text 
          fontSize="xs" 
          color={value.length > 950 ? "red.300" : "yellow.300"}
          textAlign="right"
          mt={1}
        >
          {value.length}/1000文字
        </Text>
      )}
    </Box>
  );
} 