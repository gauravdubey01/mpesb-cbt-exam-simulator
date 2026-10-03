$ErrorActionPreference = "Stop"

$JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.101-hotspot"
$env:JAVA_HOME = $JAVA_HOME
$ANDROID_SDK = "C:\Users\Gaurav\AppData\Local\Android\Sdk"
$BUILD_TOOLS = "$ANDROID_SDK\build-tools\36.0.0"
$PLATFORM_JAR = "$ANDROID_SDK\platforms\android-36\android.jar"

$env:PATH = "$JAVA_HOME\bin;$BUILD_TOOLS;" + $env:PATH

$ROOT = "E:\antigravity\exam test\android_native"
$BUILD_DIR = "$ROOT\build"
$DEX_DIR = "$BUILD_DIR\dex"
$CLASSES_DIR = "$BUILD_DIR\classes"
$OUTPUT_APK = "E:\antigravity\exam test\MPESB_Patwari_CBT_Simulator_v2.apk"

Write-Host "=================================================="
Write-Host " Building MPESB Patwari CBT Simulator Android APK"
Write-Host "=================================================="

# 1. Clean build directory
if (Test-Path $BUILD_DIR) {
    Remove-Item -Recurse -Force $BUILD_DIR
}
New-Item -ItemType Directory -Force -Path $BUILD_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $DEX_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $CLASSES_DIR | Out-Null

# 2. Compile resources with aapt2
Write-Host "[1/6] Compiling Android resources..."
& aapt2.exe compile --dir "$ROOT\res" -o "$BUILD_DIR\res.zip"

# 3. Link resources and generate R.java
Write-Host "[2/6] Linking resources and generating R.java..."
& aapt2.exe link `
    -I $PLATFORM_JAR `
    "$BUILD_DIR\res.zip" `
    --manifest "$ROOT\AndroidManifest.xml" `
    --java "$ROOT\src" `
    -o "$BUILD_DIR\unaligned.apk"

# 4. Compile Java source files
Write-Host "[3/6] Compiling Java classes..."
$javaFiles = Get-ChildItem -Path "$ROOT\src" -Filter "*.java" -Recurse | ForEach-Object { $_.FullName }
& javac.exe -d $CLASSES_DIR -source 17 -target 17 -cp "$PLATFORM_JAR;$ROOT\src" $javaFiles

# 5. Convert classes to DEX bytecode using d8
Write-Host "[4/6] Converting bytecode to classes.dex..."
$classFiles = Get-ChildItem -Path $CLASSES_DIR -Filter "*.class" -Recurse | ForEach-Object { $_.FullName }
& d8.bat --lib $PLATFORM_JAR --output $DEX_DIR $classFiles

# 6. Add classes.dex and assets into unaligned.apk
Write-Host "[5/6] Packaging classes.dex and assets into APK..."
& jar.exe uf "$BUILD_DIR\unaligned.apk" -C $DEX_DIR classes.dex

Push-Location "$ROOT"
& jar.exe uf "$BUILD_DIR\unaligned.apk" assets
Pop-Location

# 7. Zipalign & Sign
Write-Host "[6/6] Zipaligning and signing APK..."
$KEYSTORE = "$BUILD_DIR\debug.keystore"
& keytool.exe -genkey -v -keystore $KEYSTORE -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"

& zipalign.exe -p -f 4 "$BUILD_DIR\unaligned.apk" "$BUILD_DIR\aligned.apk"

& apksigner.bat sign `
    --ks $KEYSTORE `
    --ks-pass pass:android `
    --ks-key-alias androiddebugkey `
    --key-pass pass:android `
    --out $OUTPUT_APK `
    "$BUILD_DIR\aligned.apk"

Write-Host "Verifying signature of final APK..."
& apksigner.bat verify $OUTPUT_APK

$apkInfo = Get-Item $OUTPUT_APK
Write-Host "=================================================="
Write-Host " SUCCESS! Android APK created successfully!"
Write-Host " Output file: $($apkInfo.FullName)"
Write-Host " Size: $([math]::Round($apkInfo.Length / 1MB, 2)) MB"
Write-Host "=================================================="
