"use client";
import React from "react";
import { Box, Flex, Heading, VStack } from "@chakra-ui/react";
import ChatInput from "./components/ChatInput";
import ChatMessage from "./components/ChatMessage";
import { useChatStore } from "./store/chat";

export default function Home() {
  const messages = useChatStore((state) => state.messages);

  return (
    <Flex minH="100vh" direction="column" bgGradient="linear(to-br, #232526, #414345)">
      <Box p={6} bg="blackAlpha.800" color="white" boxShadow="md">
        <Heading size="lg" fontWeight="bold" letterSpacing={2}>
          金沢市なんでもチャット💬
        </Heading>
      </Box>
      <Flex flex={1} direction="column" justify="flex-end" align="center" px={2}>
        <VStack w="100%" maxW="600px" spacing={4} mb={4} align="stretch">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
        </VStack>
        <Box w="100%" maxW="600px" mb={4}>
          <ChatInput />
        </Box>
      </Flex>
    </Flex>
  );
} 