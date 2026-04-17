[app]

# (str) Title of your application
title = ZQ-自动化任务系统

# (str) Package name
package.name = zqautomation

# (str) Package domain (needed for android/ios packaging)
package.domain = org.zq

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otf

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, widgets

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma seperated list of requirements to use
requirements = python3,kivy,opencv,numpy,pillow,requests,pyjnius,android

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (landscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA,SYSTEM_ALERT_WINDOW,BIND_ACCESSIBILITY_SERVICE

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, automatically skip libraries that fail to build.
android.skip_update = False

# (bool) If True, automatically add dependencies for all modules
android.add_libs_armeabi = False

# (str) Path to the keystore file
#android.keystore = ../keystore.jks

# (str) Keystore alias
#android.keyalias = mykey

# (str) Presplash background color (for android toolchain)
#android.presplash_color = #FFFFFF

# (list) Java files to add to the android project
android.add_src = java_src/

# (str) XML file to include as an intent filters in <activity><intent-filter> tag
#android.intent_filters =

# (str) launchMode to use for the main activity
android.launch_mode = singleTask

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The output directory for the final apk/android project
#android.entry_point = org.kivy.android.PythonActivity

# (str) The java project name, this is used for ant project naming
#android.project_name = zqautomation

# (str) Path to the directory containing the android project
#android.project_dir = android-project

# (str) Path to the file containing the android entry point
#android.entry_point = org/kivy/android/PythonActivity.java

# (str) Java folder location
#android.java_build_dir = java_build

# (str) The directory where the gradle build output will be placed
#android.gradle_output_dir = gradle_output

# (str) The directory where the gradle cache will be placed
#android.gradle_cache_dir = gradle_cache

# (str) Gradle dependencies
android.gradle_dependencies = com.android.support:support-v4:28.0.0

# (list) Java jars to be included in the apk
#android.add_jars = foo.jar,bar.jar,path/to/jar/*

# (list) List of Java .aar files to include
#android.add_aars =

# (str) Ouyang input method (full, chinese, english)
#android.ouyang_input_method = full

# (str) The theme for the app (light or dark)
android.apptheme = "@android:style/Theme.Material.Light.NoActionBar"

# (list) Custom entries to the AndroidManifest.xml
#android.manifest.entries = <uses-feature android:name="android.hardware.camera" android:required="true"/>

# (str) Gradle meta data
#android.gradle_build_meta = android { compileOptions { sourceCompatibility JavaVersion.VERSION_1_8 targetCompatibility JavaVersion.VERSION_1_8 } }

# (bool) enables the given manifest place holders
#android.manifest_placeholders = foo:bar

# (bool) enables the use of the android logcat
#android.logcat = True

# (bool) enables the use of the android service
#android.service = False

# (str) The name of the service
#android.service_name = PythonService

# (str) The directory where the service will be placed
#android.service_dir = service

# (bool) enables the use of the android broadcast receiver
#android.broadcast_receiver = False

# (str) The name of the broadcast receiver
#android.broadcast_receiver_name = PythonBroadcastReceiver

# (str) The directory where the broadcast receiver will be placed
#android.broadcast_receiver_dir = broadcast_receiver

# (bool) enables the use of the android content provider
#android.content_provider = False

# (str) The name of the content provider
#android.content_provider_name = PythonContentProvider

# (str) The directory where the content provider will be placed
#android.content_provider_dir = content_provider

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
