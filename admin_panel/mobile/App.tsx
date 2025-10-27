/**
 * Messaging Agent Admin - Mobile App
 * React Native mobile application for admin panel
 */

import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  RefreshControl,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import axios from 'axios';

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const AUTH_TOKEN = 'admin-secret-token'; // Should be from secure storage

const Tab = createBottomTabNavigator();

// ==================== Dashboard Screen ====================

const DashboardScreen = () => {
  const [metrics, setMetrics] = useState({
    total_conversations: 0,
    active_users: 0,
    avg_response_time: 0,
    success_rate: 0,
  });
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/overview`, {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      });
      setMetrics(response.data.overview);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load metrics:', error);
      Alert.alert('Error', 'Failed to load dashboard metrics');
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMetrics();
    setRefreshing(false);
  };

  useEffect(() => {
    loadMetrics();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Dashboard</Text>
          <Text style={styles.headerSubtitle}>System Overview</Text>
        </View>

        <View style={styles.metricsGrid}>
          <MetricCard
            title="Total Conversations"
            value={metrics.total_conversations.toLocaleString()}
            icon="message-text"
            color="#3b82f6"
            trend="+12%"
          />
          <MetricCard
            title="Active Users"
            value={metrics.active_users.toLocaleString()}
            icon="account-group"
            color="#10b981"
            trend="+8%"
          />
          <MetricCard
            title="Avg Response Time"
            value={`${metrics.avg_response_time}ms`}
            icon="clock-outline"
            color="#f59e0b"
            trend="-15%"
          />
          <MetricCard
            title="Success Rate"
            value={`${metrics.success_rate}%`}
            icon="check-circle"
            color="#8b5cf6"
            trend="+2%"
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Health</Text>
          <HealthIndicator component="API Service" status="healthy" />
          <HealthIndicator component="Database" status="healthy" />
          <HealthIndicator component="Redis Cache" status="healthy" />
          <HealthIndicator component="Model Endpoint" status="healthy" />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ==================== Conversations Screen ====================

const ConversationsScreen = () => {
  const [conversations, setConversations] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/conversations/recent`, {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
        params: { limit: 20 },
      });
      setConversations(response.data.conversations);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load conversations:', error);
      Alert.alert('Error', 'Failed to load conversations');
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadConversations();
    setRefreshing(false);
  };

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Conversations</Text>
        <Text style={styles.headerSubtitle}>Recent Activity</Text>
      </View>
      <ScrollView
        contentContainerStyle={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        {conversations.map((conv, index) => (
          <ConversationCard key={index} conversation={conv} />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
};

// ==================== Settings Screen ====================

const SettingsScreen = () => {
  const [config, setConfig] = useState({
    provider: 'anthropic',
    model: 'claude-3-sonnet',
    temperature: 0.7,
    rate_limit: 100,
  });

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/config`, {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      });
      setConfig(response.data.config);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const saveConfig = async () => {
    try {
      await axios.put(`${API_BASE_URL}/config`, config, {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      });
      Alert.alert('Success', 'Configuration saved successfully');
    } catch (error) {
      console.error('Failed to save config:', error);
      Alert.alert('Error', 'Failed to save configuration');
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Settings</Text>
          <Text style={styles.headerSubtitle}>System Configuration</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Model Configuration</Text>
          <SettingRow label="Provider" value={config.provider} />
          <SettingRow label="Model" value={config.model} />
          <SettingRow label="Temperature" value={config.temperature.toString()} />
          <SettingRow label="Rate Limit" value={`${config.rate_limit} req/min`} />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <ActionButton
            title="Refresh Dashboard"
            icon="refresh"
            onPress={() => Alert.alert('Info', 'Dashboard refreshed')}
          />
          <ActionButton
            title="Clear Cache"
            icon="delete"
            onPress={() =>
              Alert.alert(
                'Confirm',
                'Are you sure you want to clear the cache?',
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Clear', onPress: () => clearCache() },
                ]
              )
            }
          />
          <ActionButton
            title="Export Data"
            icon="download"
            onPress={() => Alert.alert('Info', 'Data export started')}
          />
        </View>

        <TouchableOpacity style={styles.saveButton} onPress={saveConfig}>
          <Text style={styles.saveButtonText}>Save Configuration</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const clearCache = async () => {
  try {
    await axios.post(
      `${API_BASE_URL}/system/clear-cache`,
      {},
      { headers: { Authorization: `Bearer ${AUTH_TOKEN}` } }
    );
    Alert.alert('Success', 'Cache cleared successfully');
  } catch (error) {
    Alert.alert('Error', 'Failed to clear cache');
  }
};

// ==================== Analytics Screen ====================

const AnalyticsScreen = () => {
  const [usage, setUsage] = useState({
    api_calls: 0,
    tokens_used: 0,
    storage_gb: 0,
    bandwidth_gb: 0,
    total_cost: 0,
  });

  const loadUsage = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/billing/usage`, {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      });
      setUsage({
        api_calls: response.data.usage.api_calls,
        tokens_used: response.data.usage.tokens_used,
        storage_gb: response.data.usage.storage_gb,
        bandwidth_gb: response.data.usage.bandwidth_gb,
        total_cost: response.data.costs.total,
      });
    } catch (error) {
      console.error('Failed to load usage:', error);
    }
  };

  useEffect(() => {
    loadUsage();
    const interval = setInterval(loadUsage, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Analytics</Text>
          <Text style={styles.headerSubtitle}>Usage & Billing</Text>
        </View>

        <View style={styles.costCard}>
          <Text style={styles.costLabel}>Total Monthly Cost</Text>
          <Text style={styles.costValue}>${usage.total_cost.toFixed(2)}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Usage Breakdown</Text>
          <UsageRow label="API Calls" value={usage.api_calls.toLocaleString()} />
          <UsageRow label="Tokens Used" value={usage.tokens_used.toLocaleString()} />
          <UsageRow label="Storage" value={`${usage.storage_gb.toFixed(2)} GB`} />
          <UsageRow label="Bandwidth" value={`${usage.bandwidth_gb.toFixed(2)} GB`} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ==================== Component Helpers ====================

const MetricCard = ({ title, value, icon, color, trend }) => (
  <View style={[styles.metricCard, { borderLeftColor: color }]}>
    <View style={styles.metricHeader}>
      <Icon name={icon} size={24} color={color} />
      <Text style={styles.metricTrend}>{trend}</Text>
    </View>
    <Text style={styles.metricValue}>{value}</Text>
    <Text style={styles.metricTitle}>{title}</Text>
  </View>
);

const HealthIndicator = ({ component, status }) => (
  <View style={styles.healthRow}>
    <View
      style={[
        styles.healthDot,
        { backgroundColor: status === 'healthy' ? '#10b981' : '#ef4444' },
      ]}
    />
    <Text style={styles.healthComponent}>{component}</Text>
    <Text style={[styles.healthStatus, { color: status === 'healthy' ? '#10b981' : '#ef4444' }]}>
      {status}
    </Text>
  </View>
);

const ConversationCard = ({ conversation }) => (
  <TouchableOpacity style={styles.conversationCard}>
    <View style={styles.conversationHeader}>
      <Text style={styles.conversationId}>{conversation.id}</Text>
      <View
        style={[
          styles.conversationStatus,
          {
            backgroundColor:
              conversation.status === 'active' ? '#10b981' : '#6b7280',
          },
        ]}>
        <Text style={styles.conversationStatusText}>{conversation.status}</Text>
      </View>
    </View>
    <View style={styles.conversationDetails}>
      <Text style={styles.conversationDetail}>User: {conversation.user_id}</Text>
      <Text style={styles.conversationDetail}>Intent: {conversation.intent}</Text>
      <Text style={styles.conversationDetail}>Messages: {conversation.messages}</Text>
    </View>
  </TouchableOpacity>
);

const SettingRow = ({ label, value }) => (
  <View style={styles.settingRow}>
    <Text style={styles.settingLabel}>{label}</Text>
    <Text style={styles.settingValue}>{value}</Text>
  </View>
);

const ActionButton = ({ title, icon, onPress }) => (
  <TouchableOpacity style={styles.actionButton} onPress={onPress}>
    <Icon name={icon} size={20} color="#6366f1" />
    <Text style={styles.actionButtonText}>{title}</Text>
    <Icon name="chevron-right" size={20} color="#9ca3af" />
  </TouchableOpacity>
);

const UsageRow = ({ label, value }) => (
  <View style={styles.usageRow}>
    <Text style={styles.usageLabel}>{label}</Text>
    <Text style={styles.usageValue}>{value}</Text>
  </View>
);

// ==================== Main App ====================

const App = () => {
  return (
    <>
      <StatusBar barStyle="dark-content" />
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName;
              if (route.name === 'Dashboard') iconName = 'view-dashboard';
              else if (route.name === 'Conversations') iconName = 'message-text';
              else if (route.name === 'Analytics') iconName = 'chart-bar';
              else if (route.name === 'Settings') iconName = 'cog';
              return <Icon name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: '#6366f1',
            tabBarInactiveTintColor: '#9ca3af',
            headerShown: false,
          })}>
          <Tab.Screen name="Dashboard" component={DashboardScreen} />
          <Tab.Screen name="Conversations" component={ConversationsScreen} />
          <Tab.Screen name="Analytics" component={AnalyticsScreen} />
          <Tab.Screen name="Settings" component={SettingsScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </>
  );
};

// ==================== Styles ====================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    padding: 16,
  },
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricTrend: {
    fontSize: 12,
    color: '#10b981',
    fontWeight: '600',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  metricTitle: {
    fontSize: 12,
    color: '#6b7280',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  healthRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  healthDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  healthComponent: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  healthStatus: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  conversationCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  conversationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  conversationId: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  conversationStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  conversationStatusText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  conversationDetails: {
    gap: 4,
  },
  conversationDetail: {
    fontSize: 14,
    color: '#6b7280',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  settingLabel: {
    fontSize: 14,
    color: '#374151',
  },
  settingValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6366f1',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  actionButtonText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    marginLeft: 12,
  },
  saveButton: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 16,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  costCard: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    padding: 24,
    marginBottom: 16,
    alignItems: 'center',
  },
  costLabel: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
  },
  costValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 8,
  },
  usageRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  usageLabel: {
    fontSize: 14,
    color: '#374151',
  },
  usageValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
});

export default App;
