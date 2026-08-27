from pathlib import Path
layout=Path('app/src/main/res/layout/activity_main.xml')
s=layout.read_text()
def r(a,b,n):
    global s
    if a not in s: raise SystemExit('missing '+n)
    s=s.replace(a,b,1)
r('android:listSelector="@color/surface_2"','android:listSelector="@drawable/library_list_selector"','selector')
r('''            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="12dp"
                android:gravity="center"
                android:text=".m3u- und .m3u8-Dateien werden automatisch im ausgewählten Musikordner gesucht. PC-Pfade werden auf den Android-Musikordner abgebildet; nicht gefundene Titel werden pro Playlist angezeigt."
                android:textColor="@color/text_secondary"
                android:textSize="14sp" />
        </LinearLayout>

        <LinearLayout
            android:id="@+id/emptyState"
''','''            <Button
                android:id="@+id/infoSettingsButton"
                android:layout_width="match_parent"
                android:layout_height="56dp"
                android:layout_marginTop="12dp"
                android:background="@drawable/rounded_surface"
                android:text="INFOS &amp; EINSTELLUNGEN"
                android:textColor="@color/accent"
                android:textStyle="bold" />
        </LinearLayout>

        <LinearLayout
            android:id="@+id/infoSettingsPanel"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:gravity="center_horizontal"
            android:orientation="vertical"
            android:padding="32dp"
            android:visibility="gone">

            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="28dp"
                android:gravity="center"
                android:text="Developed by Eugen"
                android:textColor="@color/text_primary"
                android:textSize="18sp"
                android:textStyle="bold" />
        </LinearLayout>

        <LinearLayout
            android:id="@+id/emptyState"
''','info ui')
layout.write_text(s)
sel=Path('app/src/main/res/drawable/library_list_selector.xml')
sel.write_text('''<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true" android:drawable="@color/surface_2" />
    <item android:drawable="@android:color/transparent" />
</selector>
''')
b=Path('app/build.gradle')
t=b.read_text()
if 'versionCode 17' not in t or "versionName '0.13.3-debug'" not in t: raise SystemExit('version target missing')
t=t.replace('versionCode 17','versionCode 18',1).replace("versionName '0.13.3-debug'","versionName '0.14.0-debug'",1)
b.write_text(t)
