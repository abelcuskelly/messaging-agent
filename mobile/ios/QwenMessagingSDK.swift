//
//  QwenMessagingSDK.swift
//  iOS SDK for Qwen Messaging Agent
//
//  Complete SDK for iOS applications with authentication, caching, and error handling
//

import Foundation
import Combine

// MARK: - Models

public struct ChatMessage: Codable {
    public let role: String
    public let content: String
    public let timestamp: Date
    
    public init(role: String, content: String, timestamp: Date = Date()) {
        self.role = role
        self.content = content
        self.timestamp = timestamp
    }
}

public struct ChatRequest: Codable {
    public let message: String
    public let conversationId: String?
    public let useCache: Bool
    
    enum CodingKeys: String, CodingKey {
        case message
        case conversationId = "conversation_id"
        case useCache = "use_cache"
    }
}

public struct ChatResponse: Codable {
    public let response: String
    public let conversationId: String
    public let traceId: String?
    public let cached: Bool
    public let durationMs: Double?
    
    enum CodingKeys: String, CodingKey {
        case response
        case conversationId = "conversation_id"
        case traceId = "trace_id"
        case cached
        case durationMs = "duration_ms"
    }
}

public struct AuthToken: Codable {
    public let accessToken: String
    public let refreshToken: String
    public let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
    }
}

// MARK: - SDK Configuration

public struct QwenSDKConfig {
    public let baseURL: String
    public let apiKey: String?
    public let enableCaching: Bool
    public let enableLogging: Bool
    public let timeout: TimeInterval
    
    public init(
        baseURL: String,
        apiKey: String? = nil,
        enableCaching: Bool = true,
        enableLogging: Bool = false,
        timeout: TimeInterval = 30
    ) {
        self.baseURL = baseURL
        self.apiKey = apiKey
        self.enableCaching = enableCaching
        self.enableLogging = enableLogging
        self.timeout = timeout
    }
}

// MARK: - SDK Error

public enum QwenSDKError: Error, LocalizedError {
    case invalidURL
    case networkError(Error)
    case authenticationFailed
    case invalidResponse
    case serverError(String)
    case rateLimitExceeded
    case timeout
    
    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .authenticationFailed:
            return "Authentication failed"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let message):
            return "Server error: \(message)"
        case .rateLimitExceeded:
            return "Rate limit exceeded"
        case .timeout:
            return "Request timeout"
        }
    }
}

// MARK: - Main SDK

public class QwenMessagingSDK {
    
    private let config: QwenSDKConfig
    private var accessToken: String?
    private var refreshToken: String?
    private let session: URLSession
    private var conversations: [String: [ChatMessage]] = [:]
    private let cache = NSCache<NSString, AnyObject>()
    
    // Combine publishers
    public let messagePublisher = PassthroughSubject<ChatMessage, Never>()
    public let errorPublisher = PassthroughSubject<QwenSDKError, Never>()
    
    public init(config: QwenSDKConfig) {
        self.config = config
        
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = config.timeout
        configuration.timeoutIntervalForResource = config.timeout * 2
        self.session = URLSession(configuration: configuration)
        
        if config.enableLogging {
            print("[QwenSDK] Initialized with base URL: \(config.baseURL)")
        }
    }
    
    // MARK: - Authentication
    
    public func login(username: String, password: String) async throws {
        let url = URL(string: "\(config.baseURL)/auth/token")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        let body = "username=\(username)&password=\(password)"
        request.httpBody = body.data(using: .utf8)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw QwenSDKError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw QwenSDKError.authenticationFailed
        }
        
        let authToken = try JSONDecoder().decode(AuthToken.self, from: data)
        self.accessToken = authToken.accessToken
        self.refreshToken = authToken.refreshToken
        
        if config.enableLogging {
            print("[QwenSDK] Login successful")
        }
    }
    
    public func logout() async throws {
        guard let token = accessToken else { return }
        
        let url = URL(string: "\(config.baseURL)/auth/logout")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        _ = try await session.data(for: request)
        
        self.accessToken = nil
        self.refreshToken = nil
        self.conversations.removeAll()
        
        if config.enableLogging {
            print("[QwenSDK] Logged out")
        }
    }
    
    // MARK: - Chat
    
    public func sendMessage(
        _ message: String,
        conversationId: String? = nil,
        useCache: Bool = true
    ) async throws -> ChatResponse {
        
        // Check cache first
        if useCache && config.enableCaching {
            let cacheKey = message.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
            if let cached = cache.object(forKey: cacheKey as NSString) as? ChatResponse {
                if config.enableLogging {
                    print("[QwenSDK] Cache hit for message")
                }
                return cached
            }
        }
        
        // Prepare request
        let url = URL(string: "\(config.baseURL)/chat")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add authentication
        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else if let apiKey = config.apiKey {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        
        // Encode body
        let chatRequest = ChatRequest(
            message: message,
            conversationId: conversationId,
            useCache: useCache
        )
        request.httpBody = try JSONEncoder().encode(chatRequest)
        
        // Send request
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw QwenSDKError.invalidResponse
        }
        
        // Handle errors
        switch httpResponse.statusCode {
        case 200:
            let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
            
            // Cache response
            if useCache && config.enableCaching {
                let cacheKey = message.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
                cache.setObject(chatResponse as AnyObject, forKey: cacheKey as NSString)
            }
            
            // Update conversation history
            let convId = chatResponse.conversationId
            if conversations[convId] == nil {
                conversations[convId] = []
            }
            conversations[convId]?.append(ChatMessage(role: "user", content: message))
            conversations[convId]?.append(ChatMessage(role: "assistant", content: chatResponse.response))
            
            // Publish message
            messagePublisher.send(ChatMessage(role: "assistant", content: chatResponse.response))
            
            if config.enableLogging {
                print("[QwenSDK] Message sent successfully. Cached: \(chatResponse.cached)")
            }
            
            return chatResponse
            
        case 401:
            throw QwenSDKError.authenticationFailed
        case 429:
            throw QwenSDKError.rateLimitExceeded
        case 500...599:
            throw QwenSDKError.serverError("Server error: \(httpResponse.statusCode)")
        default:
            throw QwenSDKError.invalidResponse
        }
    }
    
    // MARK: - Conversation Management
    
    public func getConversationHistory(_ conversationId: String) -> [ChatMessage]? {
        return conversations[conversationId]
    }
    
    public func clearConversation(_ conversationId: String) {
        conversations.removeValue(forKey: conversationId)
    }
    
    public func clearAllConversations() {
        conversations.removeAll()
    }
    
    // MARK: - Cache Management
    
    public func clearCache() {
        cache.removeAllObjects()
        if config.enableLogging {
            print("[QwenSDK] Cache cleared")
        }
    }
}

// MARK: - SwiftUI Integration

#if canImport(SwiftUI)
import SwiftUI

@available(iOS 13.0, *)
public class QwenChatViewModel: ObservableObject {
    @Published public var messages: [ChatMessage] = []
    @Published public var isLoading: Bool = false
    @Published public var errorMessage: String?
    
    private let sdk: QwenMessagingSDK
    private var conversationId: String?
    private var cancellables = Set<AnyCancellable>()
    
    public init(sdk: QwenMessagingSDK) {
        self.sdk = sdk
        
        // Subscribe to message updates
        sdk.messagePublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] message in
                self?.messages.append(message)
            }
            .store(in: &cancellables)
        
        sdk.errorPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] error in
                self?.errorMessage = error.localizedDescription
            }
            .store(in: &cancellables)
    }
    
    public func sendMessage(_ text: String) {
        isLoading = true
        errorMessage = nil
        
        // Add user message immediately
        messages.append(ChatMessage(role: "user", content: text))
        
        Task {
            do {
                let response = try await sdk.sendMessage(
                    text,
                    conversationId: conversationId
                )
                
                // Store conversation ID
                if conversationId == nil {
                    conversationId = response.conversationId
                }
                
                await MainActor.run {
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    public func clearChat() {
        messages.removeAll()
        conversationId = nil
        errorMessage = nil
    }
}
#endif
