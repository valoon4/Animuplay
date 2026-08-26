#!/bin/sh
APP_HOME=$(CDPATH= cd -- "$(dirname -- "$0")" >/dev/null 2>&1 && pwd -P)
if [ -n "${JAVA_HOME:-}" ]; then
  JAVA_EXE="$JAVA_HOME/bin/java"
else
  JAVA_EXE=java
fi
if ! command -v "$JAVA_EXE" >/dev/null 2>&1 && [ ! -x "$JAVA_EXE" ]; then
  echo "ERROR: Java not found. Install JDK 17 and/or set JAVA_HOME." >&2
  exit 1
fi
exec "$JAVA_EXE" ${JAVA_OPTS:-} ${GRADLE_OPTS:-} -Dorg.gradle.appname=gradlew -classpath "$APP_HOME/gradle/wrapper/gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain "$@"
