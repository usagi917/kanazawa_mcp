import { 
  Box, 
  Spinner, 
  Text, 
  VStack,
  Container 
} from '@chakra-ui/react';

export default function Loading() {
  return (
    <Container maxW="container.md" centerContent>
      <Box
        minH="100vh"
        display="flex"
        alignItems="center"
        justifyContent="center"
        bgGradient="linear(to-br, #232526, #414345)"
        color="white"
      >
        <VStack spacing={6}>
          <Spinner
            thickness="4px"
            speed="0.65s"
            emptyColor="whiteAlpha.200"
            color="pink.500"
            size="xl"
          />
          
          <Text fontSize="lg" color="whiteAlpha.800">
            読み込み中...
          </Text>
          
          <Text fontSize="sm" color="whiteAlpha.600">
            金沢市の情報を準備しています
          </Text>
        </VStack>
      </Box>
    </Container>
  );
} 