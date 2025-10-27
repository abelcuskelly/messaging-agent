# Messaging Agent Admin - Mobile App

Native iOS and Android mobile application for managing and monitoring your messaging agent system on the go.

## 📱 Features

### Dashboard
- **Real-time Metrics**: View total conversations, active users, response times, and success rates
- **System Health**: Monitor API, database, cache, and model endpoint status
- **Auto-refresh**: Automatic updates every 30 seconds
- **Pull-to-refresh**: Manual refresh with pull-down gesture

### Conversations
- **Recent Activity**: View last 20 conversations
- **Conversation Details**: User ID, intent, message count, and status
- **Real-time Updates**: Auto-refreshing list
- **Status Indicators**: Active/completed status badges

### Analytics
- **Usage Tracking**: API calls, tokens, storage, and bandwidth
- **Cost Monitoring**: Real-time cost calculations
- **Monthly Breakdown**: Detailed usage metrics
- **Trend Analysis**: Visual charts and graphs

### Settings
- **Model Configuration**: View current provider and model settings
- **Quick Actions**: Refresh, clear cache, export data
- **System Controls**: Restart services, update configuration

## 🚀 Quick Start

### Prerequisites

```bash
# Node.js 16+
node --version

# React Native CLI
npm install -g react-native-cli

# iOS (Mac only)
xcode-select --install
sudo gem install cocoapods

# Android Studio (for Android development)
# Download from: https://developer.android.com/studio
```

### Installation

1. **Install Dependencies**:
```bash
cd admin_panel/mobile
npm install

# iOS only
cd ios && pod install && cd ..
```

2. **Configure API**:
```typescript
// In App.tsx, update:
const API_BASE_URL = 'https://your-admin-api.com/api';
const AUTH_TOKEN = 'your-admin-token';

// For secure storage, use:
import AsyncStorage from '@react-native-async-storage/async-storage';
```

3. **Run on iOS**:
```bash
npm run ios
# or
npx react-native run-ios
```

4. **Run on Android**:
```bash
npm run android
# or
npx react-native run-android
```

## 📱 Supported Platforms

- **iOS**: 13.0+
- **Android**: API 21+ (Android 5.0+)

## 🎨 Screenshots

### Dashboard
- Metric cards with real-time data
- System health indicators
- Color-coded status indicators

### Conversations
- Scrollable list of recent conversations
- Status badges (active/completed)
- Swipe gestures for actions

### Analytics
- Large cost display card
- Usage breakdown table
- Trend indicators

### Settings
- Configuration overview
- Quick action buttons
- Save/update configuration

## 🔧 Development

### Project Structure
```
mobile/
├── App.tsx                 # Main application component
├── package.json            # Dependencies
├── ios/                    # iOS-specific code
├── android/                # Android-specific code
└── README.md              # This file
```

### Key Components

**DashboardScreen**: Main dashboard with metrics and health status
**ConversationsScreen**: Recent conversations list
**AnalyticsScreen**: Usage and billing information
**SettingsScreen**: Configuration and quick actions

### API Integration

All API calls use axios with Bearer token authentication:

```typescript
const response = await axios.get(`${API_BASE_URL}/endpoint`, {
  headers: { Authorization: `Bearer ${AUTH_TOKEN}` }
});
```

### State Management

Uses React hooks for local state:
- `useState`: Component state
- `useEffect`: Data fetching and intervals
- `RefreshControl`: Pull-to-refresh

## 🎨 Customization

### Change Theme Colors

```typescript
// In styles, update colors:
tabBarActiveTintColor: '#6366f1',  // Primary color
metricCard borderLeftColor: color,  // Metric card accent
```

### Update Refresh Intervals

```typescript
// In each screen, update interval:
const interval = setInterval(loadData, 30000); // 30 seconds
```

### Add New Screens

```typescript
// In App.tsx, add to Tab.Navigator:
<Tab.Screen name="NewScreen" component={NewScreenComponent} />
```

## 🔒 Security

### Token Storage

Use secure storage for authentication tokens:

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Save token
await AsyncStorage.setItem('admin_token', token);

// Retrieve token
const token = await AsyncStorage.getItem('admin_token');
```

### API Security

- Always use HTTPS in production
- Implement token refresh logic
- Handle token expiration gracefully

## 📊 Performance

### Optimization Tips

1. **Lazy Loading**: Load data on-demand
2. **Memoization**: Use React.memo for expensive components
3. **Virtual Lists**: Use FlatList for long lists
4. **Image Optimization**: Optimize images and icons
5. **Bundle Size**: Minimize dependencies

## 🐛 Troubleshooting

### iOS Build Issues

```bash
# Clean build
cd ios
pod deintegrate
pod install
cd ..
rm -rf ios/build
```

### Android Build Issues

```bash
# Clean Gradle
cd android
./gradlew clean
cd ..
rm -rf android/app/build
```

### Metro Bundler Issues

```bash
# Clear cache
npx react-native start --reset-cache
```

## 📦 Building for Production

### iOS

```bash
# Open Xcode
open ios/MessagingAgentAdmin.xcworkspace

# Select Product > Archive
# Submit to App Store Connect
```

### Android

```bash
cd android
./gradlew assembleRelease

# APK location:
# android/app/build/outputs/apk/release/app-release.apk
```

## 🚢 Deployment

### TestFlight (iOS)

1. Archive in Xcode
2. Upload to App Store Connect
3. Add internal/external testers
4. Distribute build

### Google Play (Android)

1. Generate signed APK/AAB
2. Upload to Google Play Console
3. Create release
4. Submit for review

## 📚 Additional Resources

- [React Native Documentation](https://reactnative.dev/)
- [React Navigation](https://reactnavigation.org/)
- [iOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Android Material Design](https://material.io/design)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both iOS and Android
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details
