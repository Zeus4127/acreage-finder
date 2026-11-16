package au.zac.acreagefinder;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Acreage Finder: the land finder page in a WebView. Shows the newest listings it has, and fetches
 *  fresh ones (refreshed hourly by the scanner) in the background each time it is opened. */
public class MainActivity extends Activity {
    static final String BASE =
        "https://raw.githubusercontent.com/Zeus4127/bargain-finder/ccr-37547555-829az5/acreage/";
    static final String DATA_URL = BASE + "acreage-data.js";
    static final long CHECK_EVERY_MS = 15 * 60 * 1000L;
    WebView web;
    long lastCheck = 0;
    final Handler ui = new Handler(Looper.getMainLooper());

    File dataFile() { return new File(getFilesDir(), "acreage-data.js"); }

    File crashFile() { return new File(getFilesDir(), "last-crash.txt"); }

    /** A plain text screen, used when something goes wrong, so there's always something to read and screenshot. */
    void showMessage(String title, String body) {
        android.widget.ScrollView sv = new android.widget.ScrollView(this);
        android.widget.TextView tv = new android.widget.TextView(this);
        int pad = (int) (20 * getResources().getDisplayMetrics().density);
        tv.setPadding(pad, pad * 3, pad, pad);
        tv.setTextSize(15); tv.setTextColor(0xFF13201B); tv.setTextIsSelectable(true);
        tv.setText(title + "\n\n" + body);
        sv.setBackgroundColor(0xFFFFFFFF); sv.addView(tv); setContentView(sv);
    }

    static final String WEBSITE = "https://claude.ai/artifact/8MPdWAJGMGGWvUNDMK8AF8";

    /** Shown if the page keeps crashing on this phone: what to try, and a way to open the website instead. */
    void showHelp() {
        android.widget.LinearLayout l = new android.widget.LinearLayout(this);
        l.setOrientation(android.widget.LinearLayout.VERTICAL);
        int pad = (int) (20 * getResources().getDisplayMetrics().density);
        l.setPadding(pad, pad * 3, pad, pad); l.setBackgroundColor(0xFFFFFFFF);
        android.widget.TextView tv = new android.widget.TextView(this);
        tv.setTextSize(16); tv.setTextColor(0xFF13201B);
        tv.setText("Acreage Finder couldn't open its page on this phone.\n\n"
            + "1. Open the Play Store, search \"Android System WebView\" and \"Chrome\", and tap Update on both.\n"
            + "2. Restart the phone, then tap Try again.\n\n"
            + "Or open the same website in your browser (sign in to Claude if it asks).\n\n"
            + "Phone: Android " + android.os.Build.VERSION.RELEASE + ", " + android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL);
        l.addView(tv);
        android.widget.Button again = new android.widget.Button(this); again.setText("Try again");
        again.setOnClickListener(new android.view.View.OnClickListener() { public void onClick(android.view.View v) { recreate(); } });
        android.widget.Button site = new android.widget.Button(this); site.setText("Open the website instead");
        site.setOnClickListener(new android.view.View.OnClickListener() { public void onClick(android.view.View v) {
            try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(WEBSITE))); } catch (Exception e) { } } });
        l.addView(again); l.addView(site);
        setContentView(l);
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        // if the app ever crashes, save why, so the next launch can show it instead of just closing
        final Thread.UncaughtExceptionHandler prev = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() { public void uncaughtException(Thread t, Throwable e) {
            try (FileOutputStream o = new FileOutputStream(crashFile())) {
                o.write(("Android " + android.os.Build.VERSION.RELEASE + " (" + android.os.Build.VERSION.SDK_INT + "), " + android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL + "\n" + android.util.Log.getStackTraceString(e)).getBytes("UTF-8"));
            } catch (Exception x) { }
            if (prev != null) prev.uncaughtException(t, e);
        }});
        File cf = crashFile();
        if (cf.exists() && cf.length() > 0) {
            final String why = readHead(cf, 6000); cf.delete();
            showMessage("Acreage Finder closed last time. This is why (screenshot it and send it to Claude):", why + "\n\nClose and reopen the app to try again.");
            return;
        }
        // crash guard: "pending" is set before the page loads and cleared once it has loaded. If it's still set,
        // the last launch died while loading (even inside the phone's WebView, which Java can't catch), so the
        // next launch uses a safer drawing mode, and after that shows a help screen instead of closing again.
        final android.content.SharedPreferences boot = getSharedPreferences("boot", MODE_PRIVATE);
        int fails = boot.getInt("fails", 0) + (boot.getBoolean("pending", false) ? 1 : 0);
        final boolean safe = boot.getBoolean("safe", false) || fails >= 1;
        if (fails >= 2) {
            boot.edit().putInt("fails", 0).putBoolean("pending", false).putBoolean("safe", true).commit();
            showHelp();
            return;
        }
        boot.edit().putInt("fails", fails).putBoolean("pending", true).commit();
        try { web = new WebView(this); }
        catch (Throwable e) {   // the phone's "Android System WebView" is missing, turned off or mid-update
            showMessage("Acreage Finder needs Android System WebView",
                "Open the Play Store, search for \"Android System WebView\", and tap Update (or Enable in Settings > Apps). Then reopen this app.\n\n" + e);
            return;
        }
        if (safe) web.setLayerType(android.view.View.LAYER_TYPE_SOFTWARE, null);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setTextZoom(100);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                if ("file".equals(u.getScheme())) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception e) { }
                return true;   // listings open in the phone's browser
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                String p = r.getUrl().toString();
                File f = dataFile();
                if (p.endsWith("/acreage-data.js") && f.length() > 100000) {
                    try { return new WebResourceResponse("application/javascript", "utf-8", new FileInputStream(f)); }
                    catch (Exception e) { }
                }
                File pg = new File(getFilesDir(), "acreage.html"), hd = new File(getFilesDir(), "history-data.js");
                if (p.endsWith("/index.html") && pg.length() > 20000) {
                    try { return new WebResourceResponse("text/html", "utf-8", new FileInputStream(pg)); } catch (Exception e) { }
                }
                if (p.endsWith("/history-data.js") && hd.length() > 10000) {
                    try { return new WebResourceResponse("application/javascript", "utf-8", new FileInputStream(hd)); } catch (Exception e) { }
                }
                return null;
            }
            @Override public void onPageFinished(WebView v, String url) {
                boot.edit().putBoolean("pending", false).putInt("fails", 0).putBoolean("safe", safe).apply();
            }
            @Override public boolean onRenderProcessGone(WebView v, android.webkit.RenderProcessGoneDetail d) {
                // the page's engine ran out of memory or crashed: show a note instead of taking the whole app down
                showMessage("The page stopped", "Close and reopen Acreage Finder. If it keeps happening, screenshot this and send it to Claude.");
                web = null; return true;
            }
        });
        web.setWebChromeClient(new android.webkit.WebChromeClient());
        // the page hands its "My rules" to the app, so background alerts follow the same rules
        web.addJavascriptInterface(new Object() {
            @android.webkit.JavascriptInterface public void setRules(String json) {
                getSharedPreferences("rules", MODE_PRIVATE).edit().putString("json", json == null ? "" : json).apply();
            }
        }, "AcreageApp");
        // newer Android draws the app under the status and navigation bars; keep the page clear of them
        web.setOnApplyWindowInsetsListener(new android.view.View.OnApplyWindowInsetsListener() {
            public android.view.WindowInsets onApplyWindowInsets(android.view.View v, android.view.WindowInsets in) {
                if (android.os.Build.VERSION.SDK_INT >= 30) {
                    android.graphics.Insets i = in.getInsets(android.view.WindowInsets.Type.systemBars() | android.view.WindowInsets.Type.displayCutout());
                    v.setPadding(i.left, i.top, i.right, i.bottom);
                }
                return in;
            }
        });
        setContentView(web);
        if (b != null) web.restoreState(b); else web.loadUrl("file:///android_asset/index.html");
        if (android.os.Build.VERSION.SDK_INT >= 33) {   // the back gesture on new Android goes back a page, then closes
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                new android.window.OnBackInvokedCallback() { public void onBackInvoked() { if (web != null && web.canGoBack()) web.goBack(); else finish(); } });
        }
        // background check for new Standouts and rule matches, shown as phone notifications
        try { AlertJob.schedule(this); } catch (Throwable e) { }
        try {
            if (android.os.Build.VERSION.SDK_INT >= 33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS") != android.content.pm.PackageManager.PERMISSION_GRANTED)
                requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, 7);
        } catch (Throwable e) { }
        new Thread(new Runnable() { public void run() { try { AlertJob.check(getApplicationContext()); } catch (Throwable e) { } } }).start();
    }

    @Override protected void onSaveInstanceState(Bundle b) { super.onSaveInstanceState(b); if (web != null) web.saveState(b); }

    @Override protected void onResume() {
        super.onResume();
        long now = System.currentTimeMillis();
        if (web != null && now - lastCheck > CHECK_EVERY_MS) { lastCheck = now; fetchNewData(); }
    }

    @Override public void onBackPressed() { if (web != null && web.canGoBack()) web.goBack(); else super.onBackPressed(); }

    /** Download the newest listings; if they are newer than what is showing, offer a one-tap refresh. */
    void fetchNewData() {
        new Thread(new Runnable() { public void run() {
            fetchFile("acreage.html", "<title>Acreage Finder", 20000);
            fetchFile("history-data.js", "window.HISTORY_DATA", 10000);
            File tmp = new File(getFilesDir(), "acreage-data.tmp");
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(DATA_URL + "?t=" + System.currentTimeMillis() / 60000).openConnection();
                c.setConnectTimeout(15000); c.setReadTimeout(60000);
                if (c.getResponseCode() != 200) return;
                try (InputStream in = c.getInputStream(); FileOutputStream out = new FileOutputStream(tmp)) {
                    byte[] buf = new byte[65536]; int n;
                    while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                }
                String head = readHead(tmp, 200);
                if (!head.startsWith("window.ACREAGE_DATA=") || tmp.length() < 100000) { tmp.delete(); return; }
                String newScan = scannedOf(head), oldScan = dataFile().exists() ? scannedOf(readHead(dataFile(), 200)) : "";
                if (newScan.equals(oldScan)) { tmp.delete(); return; }
                if (!tmp.renameTo(dataFile())) return;
                final String when = newScan;
                ui.post(new Runnable() { public void run() { if (web != null) web.evaluateJavascript(
                    "(function(){var sc=(window.ACREAGE_DATA||{}).scanned||'';if(sc>='" + when + "')return;" +
                    "var d=document.createElement('div');d.textContent='New listings are ready. Tap to refresh.';" +
                    "d.style.cssText='position:fixed;left:12px;right:12px;bottom:84px;z-index:9999;background:#14304A;color:#fff;" +
                    "padding:14px 16px;border-radius:14px;font:600 16px system-ui;text-align:center;box-shadow:0 4px 14px rgba(0,0,0,.25)';" +
                    "d.onclick=function(){location.reload()};document.body.appendChild(d)})()", null); }});
            } catch (Exception e) {
                tmp.delete();   // no internet: keep showing what we have
            }
        }}).start();
    }

    /** Download one small file of the app (page or growth data) if it looks right; used next time the page loads. */
    void fetchFile(String name, String mustStart, long minSize) {
        File tmp = new File(getFilesDir(), name + ".tmp");
        try {
            HttpURLConnection c = (HttpURLConnection) new URL(BASE + name + "?t=" + System.currentTimeMillis() / 60000).openConnection();
            c.setConnectTimeout(15000); c.setReadTimeout(60000);
            if (c.getResponseCode() != 200) return;
            try (InputStream in = c.getInputStream(); FileOutputStream out = new FileOutputStream(tmp)) {
                byte[] buf = new byte[65536]; int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            }
            if (tmp.length() >= minSize && readHead(tmp, 60).toLowerCase().startsWith(mustStart.toLowerCase())) tmp.renameTo(new File(getFilesDir(), name));
            else tmp.delete();
        } catch (Exception e) { tmp.delete(); }
    }

    static String readHead(File f, int n) {
        try (FileInputStream in = new FileInputStream(f)) { byte[] b = new byte[n]; int k = in.read(b); return k > 0 ? new String(b, 0, k, "UTF-8") : ""; }
        catch (Exception e) { return ""; }
    }
    static String scannedOf(String head) {
        int i = head.indexOf("\"scanned\":\""); if (i < 0) return "";
        int j = head.indexOf('"', i + 11); return j > i ? head.substring(i + 11, j) : "";
    }
}
