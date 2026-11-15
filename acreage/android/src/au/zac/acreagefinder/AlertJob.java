package au.zac.acreagefinder;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.job.JobInfo;
import android.app.job.JobParameters;
import android.app.job.JobScheduler;
import android.app.job.JobService;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashSet;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

/** Every few hours, even when the app is closed: download the small alerts list the scanner writes
 *  (new Standouts and new rule matches) and show a notification for each one not seen before. Free: no
 *  accounts, no other apps. The first check only remembers what is already there, so there's no flood. */
public class AlertJob extends JobService {
    static final int JOB_ID = 41;
    static final String FEED = MainActivity.BASE + "alerts-feed.json";
    static final String CHANNEL = "deals";

    public static void schedule(Context c) {
        JobScheduler js = (JobScheduler) c.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if (js == null) return;
        for (JobInfo j : js.getAllPendingJobs()) if (j.getId() == JOB_ID) return;   // already scheduled
        JobInfo.Builder b = new JobInfo.Builder(JOB_ID, new ComponentName(c, AlertJob.class))
            .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
            .setPeriodic(3 * 60 * 60 * 1000L)            // about every 3 hours (Android picks the exact time)
            .setPersisted(true);                          // keeps going after the phone restarts
        js.schedule(b.build());
    }

    @Override public boolean onStartJob(final JobParameters params) {
        new Thread(new Runnable() { public void run() {
            try { check(getApplicationContext()); } catch (Exception e) { }
            jobFinished(params, false);
        }}).start();
        return true;
    }

    @Override public boolean onStopJob(JobParameters params) { return true; }

    /** Standouts always; otherwise only blocks that match the rules set on this phone (same rules as the page).
     *  With no rules on the phone, the scanner's own picks only (as before). */
    static boolean wanted(JSONObject a, JSONObject r) {
        JSONObject m = a.optJSONObject("m");
        if (m == null) return true;                       // older feed entries
        if (m.optInt("star") == 1) return true;
        if (r == null) return a.optInt("def", 1) == 1;
        double p = m.optDouble("p", 0), ac = m.optDouble("a", 0);
        if (r.optDouble("maxPrice", 0) > 0 && !(p > 0 && p <= r.optDouble("maxPrice"))) return false;
        if (r.optDouble("minAcres", 0) > 0 && ac < r.optDouble("minAcres")) return false;
        if (r.optDouble("maxAcres", 0) > 0 && ac > r.optDouble("maxAcres")) return false;
        if (r.optDouble("maxTownKm", 0) > 0 && m.optDouble("tk", 9999) > r.optDouble("maxTownKm")) return false;
        if (r.optDouble("maxCityKm", 0) > 0 && m.optDouble("ck", 9999) > r.optDouble("maxCityKm")) return false;
        if (r.optDouble("minRain", 0) > 0 && m.optDouble("rain", 0) < r.optDouble("minRain")) return false;
        String st = r.optString("states", "").trim();
        if (!st.isEmpty() && !(" " + st + " ").contains(" " + m.optString("s") + " ")) return false;
        String house = r.optString("house", "");
        if (house.equals("yes") && m.optInt("house") != 1) return false;
        if (house.equals("no") && m.optInt("house") == 1) return false;
        String deal = r.optString("deal", ""), v = m.optString("v", "");
        if (deal.equals("good") && !(v.equals("good") || v.equals("great"))) return false;
        if (deal.equals("great") && !v.equals("great")) return false;
        if (r.optBoolean("water") && m.optInt("water") != 1) return false;
        if (r.optBoolean("noFlood") && m.optInt("flood") == 1) return false;
        if (r.optBoolean("noVeg") && m.optInt("veg") == 1) return false;
        if (r.optBoolean("noFire") && m.optInt("fire") == 1) return false;
        if (r.optBoolean("stay") && m.optInt("stay") != 1) return false;
        if (r.optBoolean("split") && m.optInt("lots") < 2) return false;
        if (r.optBoolean("musts") && m.optInt("gok") != 1) return false;
        if (r.optBoolean("g60") && m.optInt("gs") < 60) return false;
        return true;
    }

    static void check(Context c) throws Exception {
        HttpURLConnection con = (HttpURLConnection) new URL(FEED + "?t=" + System.currentTimeMillis() / 60000).openConnection();
        con.setConnectTimeout(15000); con.setReadTimeout(30000);
        if (con.getResponseCode() != 200) return;
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (InputStream in = con.getInputStream()) { byte[] buf = new byte[16384]; int n; while ((n = in.read(buf)) > 0) out.write(buf, 0, n); }
        JSONArray alerts = new JSONObject(out.toString("UTF-8")).optJSONArray("alerts");
        if (alerts == null) return;
        SharedPreferences sp = c.getSharedPreferences("alerts", Context.MODE_PRIVATE);
        Set<String> seen = new HashSet<String>(sp.getStringSet("seen", new HashSet<String>()));
        boolean first = !sp.getBoolean("started", false);
        JSONObject rules = null;   // "My rules" from the page, saved by MainActivity
        try { String rs = c.getSharedPreferences("rules", Context.MODE_PRIVATE).getString("json", ""); if (rs.length() > 2) rules = new JSONObject(rs); } catch (Exception e) { }
        if (rules != null && rules.length() == 0) rules = null;
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26 && nm != null)
            nm.createNotificationChannel(new NotificationChannel(CHANNEL, "New deals", NotificationManager.IMPORTANCE_DEFAULT));
        int shown = 0;
        for (int i = 0; i < alerts.length(); i++) {
            JSONObject a = alerts.getJSONObject(i);
            String id = a.optString("id");
            if (id.isEmpty() || seen.contains(id)) continue;
            seen.add(id);
            if (!wanted(a, rules)) continue;
            if (first || shown >= 5 || nm == null) continue;
            String url = a.optString("url");
            Intent open = url.isEmpty() ? new Intent(c, MainActivity.class) : new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            PendingIntent pi = PendingIntent.getActivity(c, id.hashCode(), open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder nb = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(c, CHANNEL) : new Notification.Builder(c);
            nb.setSmallIcon(R.drawable.ic_notify).setContentTitle(a.optString("title", "New deal"))
              .setContentText(a.optString("text")).setStyle(new Notification.BigTextStyle().bigText(a.optString("text")))
              .setContentIntent(pi).setAutoCancel(true);
            nm.notify(id.hashCode(), nb.build());
            shown++;
        }
        sp.edit().putStringSet("seen", seen).putBoolean("started", true).apply();
    }
}
