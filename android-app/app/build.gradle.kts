plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.marcgames.iphone3gs"
    compileSdk = 35

    defaultConfig {
        applicationId = "org.marcgames.iphone3gs"
        minSdk = 26
        targetSdk = 28
        versionCode = 1
        versionName = "0.1.0-dev"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}
