"use client";
import React from "react";
import { Box, Flex, Heading, VStack, Container, Text } from "@chakra-ui/react";
import ChatInput from "./components/ChatInput";
import ChatMessage from "./components/ChatMessage";
import { useChatStore } from "./store/chat";

export default function Home() {
  const messages = useChatStore((state) => state.messages);

  return (
    <Flex 
      minH="100vh" 
      direction="column" 
      bgGradient="linear(to-br, #232526, #414345)"
      position="relative"
    >
      {/* ヘッダー */}
      <Box 
        as="header"
        p={6} 
        bg="blackAlpha.800" 
        color="white" 
        boxShadow="lg"
        borderBottom="1px solid"
        borderColor="whiteAlpha.200"
      >
        <Container maxW="container.lg">
          <Heading 
            as="h1"
            size="lg" 
            fontWeight="bold" 
            letterSpacing={1}
            textAlign="center"
          >
            🌸 金沢市なんでもチャット 💬
          </Heading>
          <Text 
            fontSize="sm" 
            color="whiteAlpha.700" 
            textAlign="center" 
            mt={2}
          >
            観光・交通・ごみ収集情報をお気軽にお尋ねください
          </Text>
        </Container>
      </Box>

      {/* メインコンテンツ */}
      <Flex 
        as="main"
        flex={1} 
        direction="column" 
        justify="flex-end" 
        align="center" 
        px={4}
        py={6}
      >
        <Container maxW="container.md" w="100%" h="100%">
          <VStack 
            spacing={4} 
            align="stretch" 
            h="100%"
            justify="flex-end"
            minH="400px"
          >
            {/* メッセージ表示エリア */}
            <VStack 
              spacing={4} 
              align="stretch"
              flex={1}
              overflowY="auto"
              maxH="calc(100vh - 250px)"
              px={2}
            >
              {messages.length === 0 ? (
                <Box 
                  textAlign="center" 
                  color="whiteAlpha.600" 
                  py={8}
                  px={4}
                >
                  <Text fontSize="lg" mb={4}>
                    👋 こんにちは！
                  </Text>
                  <Text fontSize="md" mb={6}>
                    金沢市についてなんでもお聞きください✨
                  </Text>
                  <VStack spacing={2} fontSize="sm" color="whiteAlpha.500">
                    <Text>💡 例：「兼六園について教えて」</Text>
                    <Text>💡 例：「バス停はどこにありますか？」</Text>
                    <Text>💡 例：「今日のごみ収集は？」</Text>
                  </VStack>
                </Box>
              ) : (
                messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))
              )}
            </VStack>

            {/* 入力エリア */}
            <Box mt={4}>
              <ChatInput />
            </Box>
          </VStack>
        </Container>
      </Flex>
    </Flex>
  );
} 