# Qwen Messaging Agent Mobile SDKs

Complete mobile SDKs for iOS and Android with authentication, caching, and reactive updates.

## iOS SDK

### Installation

#### Swift Package Manager
```swift
dependencies: [
    .package(url: "https://github.com/your-org/qwen-messaging-sdk-ios.git", from: "1.0.0")
]
```

#### CocoaPods
```ruby
pod 'QwenMessagingSDK', '~> 1.0'
```

### Quick Start

```swift
import QwenMessagingSDK

// Configure SDK
let config = QwenSDKConfig(
    baseURL: "https://your-api.com",
    apiKey: "your-api-key",
    enableCaching: true,
    enableLogging: true
)

let sdk = QwenMessagingSDK(config: config)

// Login
try await sdk.login(username: "user", password: "pass")

// Send message
let response = try await sdk.sendMessage("What are the ticket prices?")
print(response.response)

// Logout
try await sdk.logout()
```

### SwiftUI Integration

```swift
import SwiftUI
import QwenMessagingSDK

struct ChatView: View {
    @StateObject var viewModel: QwenChatViewModel
    @State private var messageText = ""
    
    var body: some View {
        VStack {
            // Messages list
            ScrollView {
                ForEach(viewModel.messages, id: \.timestamp) { message in
                    MessageBubble(message: message)
                }
            }
            
            // Input field
            HStack {
                TextField("Type a message", text: $messageText)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                
                Button("Send") {
                    viewModel.sendMessage(messageText)
                    messageText = ""
                }
                .disabled(viewModel.isLoading)
            }
            .padding()
        }
    }
}
```

## Android SDK

### Installation

#### Gradle
```gradle
dependencies {
    implementation 'com.qwen.messaging:sdk:1.0.0'
    implementation 'com.squareup.okhttp3:okhttp:4.12.0'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
}
```

### Quick Start

```kotlin
import com.qwen.messaging.sdk.*

// Configure SDK
val config = QwenSDKConfig(
    baseURL = "https://your-api.com",
    apiKey = "your-api-key",
    enableCaching = true,
    enableLogging = true
)

val sdk = QwenMessagingSDK(config, context)

// Login
lifecycleScope.launch {
    try {
        sdk.login("user", "pass")
        
        // Send message
        val response = sdk.sendMessage("What are the ticket prices?")
        println(response.response)
        
    } catch (e: QwenSDKError) {
        println("Error: ${e.message}")
    }
}

// Cleanup
override fun onDestroy() {
    super.onDestroy()
    sdk.cleanup()
}
```

### Jetpack Compose Integration

```kotlin
import androidx.compose.runtime.*
import com.qwen.messaging.sdk.*

@Composable
fun ChatScreen() {
    val sdk = rememberQwenSDK(config)
    var messages by remember { mutableStateOf(listOf<ChatMessage>()) }
    var messageText by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    
    // Collect messages
    LaunchedEffect(sdk) {
        sdk.messageFlow.collect { message ->
            message?.let { messages = messages + it }
        }
    }
    
    Column {
        // Messages list
        LazyColumn(modifier = Modifier.weight(1f)) {
            items(messages) { message ->
                MessageBubble(message = message)
            }
        }
        
        // Input field
        Row(modifier = Modifier.padding(16.dp)) {
            TextField(
                value = messageText,
                onValueChange = { messageText = it },
                modifier = Modifier.weight(1f)
            )
            
            Button(
                onClick = {
                    isLoading = true
                    lifecycleScope.launch {
                        try {
                            sdk.sendMessage(messageText)
                            messageText = ""
                        } finally {
                            isLoading = false
                        }
                    }
                },
                enabled = !isLoading
            ) {
                Text("Send")
            }
        }
    }
}
```

## Features

### Authentication
- OAuth2/JWT token authentication
- API key authentication
- Automatic token refresh
- Secure token storage

### Caching
- LRU cache for responses
- Configurable cache size
- Automatic cache invalidation
- Cache hit/miss tracking

### Error Handling
- Comprehensive error types
- Automatic retry logic
- Network error handling
- Rate limit detection

### Reactive Updates
- Combine (iOS) / Flow (Android)
- Real-time message updates
- Error notifications
- Loading states

### Conversation Management
- Multi-conversation support
- Message history tracking
- Conversation persistence
- Clear/delete conversations

## Configuration Options

```swift
// iOS
let config = QwenSDKConfig(
    baseURL: "https://api.example.com",
    apiKey: "optional-api-key",
    enableCaching: true,        // Enable response caching
    enableLogging: true,        // Enable debug logging
    timeout: 30                 // Request timeout in seconds
)
```

```kotlin
// Android
val config = QwenSDKConfig(
    baseURL = "https://api.example.com",
    apiKey = "optional-api-key",
    enableCaching = true,       // Enable response caching
    enableLogging = true,       // Enable debug logging
    timeout = 30,               // Request timeout in seconds
    cacheSize = 50              // LRU cache size
)
```

## Best Practices

1. **Initialize Once**: Create SDK instance once and reuse
2. **Handle Errors**: Always wrap SDK calls in try-catch
3. **Logout on Exit**: Call logout() when user exits
4. **Clear Cache**: Periodically clear cache to free memory
5. **Monitor Performance**: Track response times and cache hits

## Example Apps

See the `examples/` directory for complete sample applications:
- `ios-example/` - SwiftUI chat app
- `android-example/` - Jetpack Compose chat app

## License

MIT License
