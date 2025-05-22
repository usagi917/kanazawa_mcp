"use client";
import React from "react";
import { Box, Text, Flex, Avatar } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { ChatMessage as ChatMessageType } from "../types/chat";
import { FiUser, FiMessageSquare } from "react-icons/fi";

const MotionBox = motion(Box);

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <MotionBox
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      mb={4}
    >
      <Flex gap={3} align="flex-start" justify={isUser ? "flex-end" : "flex-start"}>
        {!isUser && (
          <Avatar
            icon={<FiMessageSquare />}
            bg="pink.500"
            color="white"
            size="sm"
          />
        )}
        <Box
          maxW="80%"
          bg={isUser ? "pink.500" : "whiteAlpha.800"}
          color={isUser ? "white" : "black"}
          p={4}
          borderRadius="xl"
          boxShadow="md"
        >
          <Text fontSize="md" whiteSpace="pre-wrap">
            {message.content}
          </Text>
        </Box>
        {isUser && (
          <Avatar
            icon={<FiUser />}
            bg="gray.500"
            color="white"
            size="sm"
          />
        )}
      </Flex>
    </MotionBox>
  );
} 