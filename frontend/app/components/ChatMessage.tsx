"use client";
import React from "react";
import { 
  Box, 
  Text, 
  Flex, 
  Avatar, 
  VStack,
  HStack,
  IconButton,
  useClipboard,
  useToast
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { ChatMessage as ChatMessageType } from "../types/chat";
import { FiUser, FiMessageSquare, FiCopy, FiCheck } from "react-icons/fi";

const MotionBox = motion(Box);

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const { onCopy, hasCopied } = useClipboard(message.content);
  const toast = useToast();

  const handleCopy = () => {
    onCopy();
    toast({
      title: "コピーしました",
      status: "success",
      duration: 2000,
      isClosable: true,
      position: "top",
      size: "sm",
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      mb={4}
      role="article"
      aria-label={`${isUser ? 'ユーザー' : 'アシスタント'}のメッセージ`}
    >
      <Flex 
        gap={3} 
        align="flex-start" 
        justify={isUser ? "flex-end" : "flex-start"}
        direction={isUser ? "row-reverse" : "row"}
      >
        {/* アバター */}
        <Avatar
          icon={isUser ? <FiUser /> : <FiMessageSquare />}
          bg={isUser ? "gray.600" : "pink.500"}
          color="white"
          size="sm"
          name={isUser ? "ユーザー" : "アシスタント"}
        />

        {/* メッセージコンテンツ */}
        <VStack 
          align={isUser ? "flex-end" : "flex-start"} 
          spacing={1}
          maxW="80%"
        >
          {/* メッセージバブル */}
          <Box
            bg={isUser ? "pink.500" : "whiteAlpha.900"}
            color={isUser ? "white" : "gray.800"}
            p={4}
            borderRadius="lg"
            boxShadow="md"
            position="relative"
            _before={{
              content: '""',
              position: "absolute",
              top: "10px",
              [isUser ? "right" : "left"]: "-8px",
              width: 0,
              height: 0,
              borderTop: "8px solid transparent",
              borderBottom: "8px solid transparent",
              [isUser ? "borderLeft" : "borderRight"]: isUser 
                ? "8px solid" 
                : "8px solid",
              [isUser ? "borderLeftColor" : "borderRightColor"]: isUser 
                ? "pink.500" 
                : "whiteAlpha.900",
            }}
            transition="all 0.2s"
            _hover={{
              transform: "translateY(-1px)",
              boxShadow: "lg"
            }}
          >
            <Text 
              fontSize="md" 
              whiteSpace="pre-wrap"
              lineHeight="1.6"
              wordBreak="break-word"
            >
              {message.content}
            </Text>
          </Box>

          {/* タイムスタンプとアクション */}
          <HStack spacing={2} justify={isUser ? "flex-end" : "flex-start"}>
            <Text 
              fontSize="xs" 
              color="whiteAlpha.600"
              fontWeight="500"
            >
              {formatTime(message.timestamp)}
            </Text>
            
            {/* コピーボタン */}
            <IconButton
              aria-label="メッセージをコピー"
              icon={hasCopied ? <FiCheck /> : <FiCopy />}
              size="xs"
              variant="ghost"
              color="whiteAlpha.600"
              _hover={{ 
                color: "whiteAlpha.800",
                bg: "whiteAlpha.100"
              }}
              onClick={handleCopy}
            />
          </HStack>
        </VStack>
      </Flex>
    </MotionBox>
  );
} 