/**
 * QwenMessagingSDK.kt
 * Android SDK for Qwen Messaging Agent
 * 
 * Complete SDK for Android applications with authentication, caching, and error handling
 */

package com.qwen.messaging.sdk

import android.content.Context
import android.util.LruCache
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

// MARK: - Data Models

data class ChatMessage(
    val role: String,
    val content: String,
    val timestamp: Long = System.currentTimeMillis()
)

data class ChatRequest(
    val message: String,
    val conversationId: String? = null,
    val useCache: Boolean = true
)

data class ChatResponse(
    val response: String,
    val conversationId: String,
    val traceId: String? = null,
    val cached: Boolean = false,
    val durationMs: Double? = null
)

data class AuthToken(
    val accessToken: String,
    val refreshToken: String,
    val tokenType: String
)

// MARK: - SDK Configuration

data class QwenSDKConfig(
    val baseURL: String,
    val apiKey: String? = null,
    val enableCaching: Boolean = true,
    val enableLogging: Boolean = false,
    val timeout: Long = 30,
    val cacheSize: Int = 50
)

// MARK: - SDK Error

sealed class QwenSDKError : Exception() {
    object InvalidURL : QwenSDKError()
    data class NetworkError(val error: Throwable) : QwenSDKError()
    object AuthenticationFailed : QwenSDKError()
    object InvalidResponse : QwenSDKError()
    data class ServerError(val message: String) : QwenSDKError()
    object RateLimitExceeded : QwenSDKError()
    object Timeout : QwenSDKError()
    
    override val message: String
        get() = when (this) {
            is InvalidURL -> "Invalid API URL"
            is NetworkError -> "Network error: ${error.message}"
            is AuthenticationFailed -> "Authentication failed"
            is InvalidResponse -> "Invalid response from server"
            is ServerError -> "Server error: $message"
            is RateLimitExceeded -> "Rate limit exceeded"
            is Timeout -> "Request timeout"
        }
}

// MARK: - Main SDK

class QwenMessagingSDK(
    private val config: QwenSDKConfig,
    private val context: Context
) {
    
    private var accessToken: String? = null
    private var refreshToken: String? = null
    
    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(config.timeout, TimeUnit.SECONDS)
        .readTimeout(config.timeout, TimeUnit.SECONDS)
        .writeTimeout(config.timeout, TimeUnit.SECONDS)
        .addInterceptor(LoggingInterceptor(config.enableLogging))
        .build()
    
    private val conversations = mutableMapOf<String, MutableList<ChatMessage>>()
    private val cache = LruCache<String, ChatResponse>(config.cacheSize)
    
    // State flows for reactive updates
    private val _messageFlow = MutableStateFlow<ChatMessage?>(null)
    val messageFlow: StateFlow<ChatMessage?> = _messageFlow
    
    private val _errorFlow = MutableStateFlow<QwenSDKError?>(null)
    val errorFlow: StateFlow<QwenSDKError?> = _errorFlow
    
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    // MARK: - Authentication
    
    suspend fun login(username: String, password: String) = withContext(Dispatchers.IO) {
        val url = "${config.baseURL}/auth/token"
        
        val formBody = FormBody.Builder()
            .add("username", username)
            .add("password", password)
            .build()
        
        val request = Request.Builder()
            .url(url)
            .post(formBody)
            .build()
        
        try {
            val response = client.newCall(request).execute()
            
            if (response.isSuccessful) {
                val json = JSONObject(response.body?.string() ?: "")
                accessToken = json.getString("access_token")
                refreshToken = json.getString("refresh_token")
                
                if (config.enableLogging) {
                    println("[QwenSDK] Login successful")
                }
            } else {
                throw QwenSDKError.AuthenticationFailed
            }
        } catch (e: IOException) {
            throw QwenSDKError.NetworkError(e)
        }
    }
    
    suspend fun logout() = withContext(Dispatchers.IO) {
        val token = accessToken ?: return@withContext
        
        val url = "${config.baseURL}/auth/logout"
        val request = Request.Builder()
            .url(url)
            .post("".toRequestBody())
            .addHeader("Authorization", "Bearer $token")
            .build()
        
        try {
            client.newCall(request).execute()
            accessToken = null
            refreshToken = null
            conversations.clear()
            
            if (config.enableLogging) {
                println("[QwenSDK] Logged out")
            }
        } catch (e: IOException) {
            throw QwenSDKError.NetworkError(e)
        }
    }
    
    // MARK: - Chat
    
    suspend fun sendMessage(
        message: String,
        conversationId: String? = null,
        useCache: Boolean = true
    ): ChatResponse = withContext(Dispatchers.IO) {
        
        // Check cache first
        if (useCache && config.enableCaching) {
            val cacheKey = message.lowercase().trim()
            cache.get(cacheKey)?.let { cached ->
                if (config.enableLogging) {
                    println("[QwenSDK] Cache hit for message")
                }
                return@withContext cached
            }
        }
        
        // Prepare request
        val url = "${config.baseURL}/chat"
        
        val json = JSONObject().apply {
            put("message", message)
            conversationId?.let { put("conversation_id", it) }
            put("use_cache", useCache)
        }
        
        val requestBody = json.toString()
            .toRequestBody("application/json".toMediaType())
        
        val request = Request.Builder()
            .url(url)
            .post(requestBody)
            .apply {
                // Add authentication
                accessToken?.let {
                    addHeader("Authorization", "Bearer $it")
                } ?: config.apiKey?.let {
                    addHeader("X-API-Key", it)
                }
            }
            .build()
        
        try {
            val response = client.newCall(request).execute()
            
            when (response.code) {
                200 -> {
                    val responseJson = JSONObject(response.body?.string() ?: "")
                    val chatResponse = ChatResponse(
                        response = responseJson.getString("response"),
                        conversationId = responseJson.getString("conversation_id"),
                        traceId = responseJson.optString("trace_id"),
                        cached = responseJson.optBoolean("cached", false),
                        durationMs = responseJson.optDouble("duration_ms")
                    )
                    
                    // Cache response
                    if (useCache && config.enableCaching) {
                        val cacheKey = message.lowercase().trim()
                        cache.put(cacheKey, chatResponse)
                    }
                    
                    // Update conversation history
                    val convId = chatResponse.conversationId
                    if (!conversations.containsKey(convId)) {
                        conversations[convId] = mutableListOf()
                    }
                    conversations[convId]?.add(ChatMessage("user", message))
                    conversations[convId]?.add(ChatMessage("assistant", chatResponse.response))
                    
                    // Emit message
                    _messageFlow.value = ChatMessage("assistant", chatResponse.response)
                    
                    if (config.enableLogging) {
                        println("[QwenSDK] Message sent. Cached: ${chatResponse.cached}")
                    }
                    
                    return@withContext chatResponse
                }
                401 -> throw QwenSDKError.AuthenticationFailed
                429 -> throw QwenSDKError.RateLimitExceeded
                in 500..599 -> throw QwenSDKError.ServerError("Server error: ${response.code}")
                else -> throw QwenSDKError.InvalidResponse
            }
        } catch (e: IOException) {
            _errorFlow.value = QwenSDKError.NetworkError(e)
            throw QwenSDKError.NetworkError(e)
        }
    }
    
    // MARK: - Conversation Management
    
    fun getConversationHistory(conversationId: String): List<ChatMessage>? {
        return conversations[conversationId]
    }
    
    fun clearConversation(conversationId: String) {
        conversations.remove(conversationId)
    }
    
    fun clearAllConversations() {
        conversations.clear()
    }
    
    // MARK: - Cache Management
    
    fun clearCache() {
        cache.evictAll()
        if (config.enableLogging) {
            println("[QwenSDK] Cache cleared")
        }
    }
    
    fun getCacheSize(): Int {
        return cache.size()
    }
    
    // MARK: - Cleanup
    
    fun cleanup() {
        scope.cancel()
    }
}

// MARK: - Logging Interceptor

private class LoggingInterceptor(private val enabled: Boolean) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        
        if (enabled) {
            println("[QwenSDK] Request: ${request.method} ${request.url}")
        }
        
        val response = chain.proceed(request)
        
        if (enabled) {
            println("[QwenSDK] Response: ${response.code} (${response.message})")
        }
        
        return response
    }
}

// MARK: - Jetpack Compose Integration

@androidx.compose.runtime.Composable
fun rememberQwenSDK(config: QwenSDKConfig): QwenMessagingSDK {
    val context = androidx.compose.ui.platform.LocalContext.current
    return androidx.compose.runtime.remember { QwenMessagingSDK(config, context) }
}
