plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.pricetyper.android"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.pricetyper.android"
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    packaging {
        jniLibs {
            excludes += setOf("**/libsherpa-onnx-c-api.so", "**/libsherpa-onnx-cxx-api.so")
        }
    }

    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/model-assets"))
}

dependencies {
    implementation("androidx.activity:activity-ktx:1.10.1")
    implementation("androidx.core:core-ktx:1.17.0")
    implementation(files("libs/sherpa-onnx-1.13.8.aar"))
}

val syncLocalModels by tasks.registering(Copy::class) {
    val repoRoot = rootProject.projectDir.parentFile
    val zipformer = repoRoot.resolve("models/sherpa-onnx-zipformer-vi-30M-int8-2026-02-09")
    val vad = repoRoot.resolve("models/silero_vad.onnx")
    from(zipformer) {
        include("encoder.int8.onnx", "decoder.onnx", "joiner.int8.onnx", "tokens.txt")
        into("model")
    }
    from(vad) {
        into("model")
        rename { "silero_vad.onnx" }
    }
    into(layout.buildDirectory.dir("generated/model-assets"))
    onlyIf { zipformer.isDirectory && vad.isFile }
}

tasks.named("preBuild").configure {
    dependsOn(syncLocalModels)
}
