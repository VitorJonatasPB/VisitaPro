const IS_STANING = process.env.APP_VARIANT === 'staning';

export default {
  "expo": {
    "name": IS_STANING ? "VisitaPro (STG)" : "VisitaPro",
    "slug": "mobile",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "scheme": "mobile",
    "userInterfaceStyle": "automatic",
    "newArchEnabled": true,
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": IS_STANING ? "com.vitor.jonatas.mobile.staning" : "com.vitor.jonatas.mobile"
    },
    "android": {
      "adaptiveIcon": {
        "backgroundColor": "#0F172A",
        "foregroundImage": "./assets/images/android-icon-foreground.png",
        "backgroundImage": "./assets/images/android-icon-background.png"
      },
      "edgeToEdgeEnabled": true,
      "predictiveBackGestureEnabled": false,
      "softwareKeyboardLayoutMode": "pan",
      "package": IS_STANING ? "com.vitor.jonatas.mobile.staning" : "com.vitor.jonatas.mobile"
    },
    "web": {
      "output": "static",
      "favicon": "./assets/images/favicon.png"
    },
    "plugins": [
      "expo-router",
      [
        "expo-splash-screen",
        {
          "image": "./assets/images/splash-icon.png",
          "imageWidth": 200,
          "resizeMode": "contain",
          "backgroundColor": "#ffffff",
          "dark": {
            "backgroundColor": "#000000"
          }
        }
      ]
    ],
    "experiments": {
      "typedRoutes": true,
      "reactCompiler": true
    },
    "extra": {
      "router": {},
      "eas": {
        "projectId": "ea7b177f-0465-4dce-b304-6032dc316c68"
      }
    },
    "runtimeVersion": {
      "policy": "appVersion"
    },
    "updates": {
      "url": "https://u.expo.dev/ea7b177f-0465-4dce-b304-6032dc316c68"
    }
  }
};
