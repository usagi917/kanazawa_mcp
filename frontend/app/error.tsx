'use client';

import { useEffect } from 'react';
import { 
  Box, 
  Button, 
  Heading, 
  Text, 
  VStack,
  Container,
  Icon
} from '@chakra-ui/react';
import { FiAlertCircle } from 'react-icons/fi';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // エラーをログに記録
    console.error('アプリケーションエラー:', error);
  }, [error]);

  return (
    <Container maxW="container.md" centerContent>
      <Box
        minH="100vh"
        display="flex"
        alignItems="center"
        justifyContent="center"
        bgGradient="linear(to-br, #232526, #414345)"
        color="white"
        px={6}
      >
        <VStack spacing={6} textAlign="center">
          <Icon as={FiAlertCircle} boxSize={16} color="red.300" />
          
          <Heading as="h1" size="lg">
            エラーが発生しました
          </Heading>
          
          <Text fontSize="md" color="whiteAlpha.700" maxW="md">
            申し訳ございません。予期しないエラーが発生しました。
            ページを再読み込みしてもう一度お試しください。
          </Text>
          
          <VStack spacing={3}>
            <Button
              colorScheme="pink"
              size="lg"
              onClick={reset}
              borderRadius="full"
            >
              もう一度試す
            </Button>
            
            <Button
              variant="ghost"
              color="whiteAlpha.700"
              onClick={() => window.location.href = '/'}
              borderRadius="full"
            >
              ホームに戻る
            </Button>
          </VStack>
          
          {process.env.NODE_ENV === 'development' && (
            <Box
              bg="blackAlpha.500"
              p={4}
              borderRadius="md"
              fontSize="xs"
              color="red.200"
              maxW="lg"
              overflow="auto"
            >
              <Text fontWeight="bold" mb={2}>開発者向け情報:</Text>
              <Text>{error.message}</Text>
            </Box>
          )}
        </VStack>
      </Box>
    </Container>
  );
} 