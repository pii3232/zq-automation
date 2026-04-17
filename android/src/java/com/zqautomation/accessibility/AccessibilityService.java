package com.zqautomation.accessibility;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.os.Build;
import android.os.Environment;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.media.MediaActionSound;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * 无障碍服务 - 实现截图、点击、滑动、文本输入
 */
public class ZQAccessibilityService extends AccessibilityService {
    private static final String TAG = "ZQAccessibility";
    private static ZQAccessibilityService instance;
    private MediaActionSound sound;
    
    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        sound = new MediaActionSound();
        Log.i(TAG, "Accessibility Service Created");
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
        if (sound != null) {
            sound.release();
        }
        Log.i(TAG, "Accessibility Service Destroyed");
    }
    
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // 不需要处理事件
    }
    
    @Override
    public void onInterrupt() {
        Log.w(TAG, "Accessibility Service Interrupted");
    }
    
    /**
     * 获取服务实例
     */
    public static ZQAccessibilityService getInstance() {
        return instance;
    }
    
    /**
     * 检查服务是否运行中
     */
    public static boolean isRunning() {
        return instance != null;
    }
    
    /**
     * 模拟点击
     */
    public boolean tap(float x, float y) {
        return tap(x, y, 100); // 默认100ms按下时长
    }
    
    /**
     * 模拟点击（指定按下时长）
     */
    public boolean tap(float x, float y, long durationMs) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            Log.e(TAG, "需要Android 7.0以上版本");
            return false;
        }
        
        Log.i(TAG, String.format("点击坐标: (%.1f, %.1f), 时长: %dms", x, y, durationMs));
        
        GestureDescription.Builder builder = new GestureDescription.Builder();
        builder.addStroke(new GestureDescription.StrokeDescription(
            android.graphics.Path.createPath(x, y, x, y),
            0,
            durationMs
        ));
        
        final CountDownLatch latch = new CountDownLatch(1);
        final boolean[] result = {false};
        
        dispatchGesture(builder.build(), new GestureResultCallback() {
            @Override
            public void onCompleted(GestureDescription gestureDescription) {
                result[0] = true;
                latch.countDown();
                Log.i(TAG, "点击完成");
            }
            
            @Override
            public void onCancelled(GestureDescription gestureDescription) {
                result[0] = false;
                latch.countDown();
                Log.w(TAG, "点击取消");
            }
        }, null);
        
        try {
            latch.await(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Log.e(TAG, "点击等待被中断", e);
            return false;
        }
        
        return result[0];
    }
    
    /**
     * 模拟滑动
     */
    public boolean swipe(float startX, float startY, float endX, float endY, long durationMs) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
            Log.e(TAG, "需要Android 7.0以上版本");
            return false;
        }
        
        Log.i(TAG, String.format("滑动: (%.1f,%.1f) -> (%.1f,%.1f), 时长: %dms", 
            startX, startY, endX, endY, durationMs));
        
        android.graphics.Path path = new android.graphics.Path();
        path.moveTo(startX, startY);
        path.lineTo(endX, endY);
        
        GestureDescription.Builder builder = new GestureDescription.Builder();
        builder.addStroke(new GestureDescription.StrokeDescription(path, 0, durationMs));
        
        final CountDownLatch latch = new CountDownLatch(1);
        final boolean[] result = {false};
        
        dispatchGesture(builder.build(), new GestureResultCallback() {
            @Override
            public void onCompleted(GestureDescription gestureDescription) {
                result[0] = true;
                latch.countDown();
                Log.i(TAG, "滑动完成");
            }
            
            @Override
            public void onCancelled(GestureDescription gestureDescription) {
                result[0] = false;
                latch.countDown();
                Log.w(TAG, "滑动取消");
            }
        }, null);
        
        try {
            latch.await(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Log.e(TAG, "滑动等待被中断", e);
            return false;
        }
        
        return result[0];
    }
    
    /**
     * 输入文本
     */
    public boolean inputText(String text) {
        if (text == null || text.isEmpty()) {
            return false;
        }
        
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) {
            Log.e(TAG, "无法获取根节点");
            return false;
        }
        
        // 查找当前焦点的编辑框
        AccessibilityNodeInfo focusNode = rootNode.findFocus(AccessibilityNodeInfo.FOCUS_INPUT);
        if (focusNode == null) {
            Log.e(TAG, "未找到焦点输入框");
            return false;
        }
        
        // 检查是否可编辑
        if (!focusNode.isEditable()) {
            Log.w(TAG, "焦点节点不可编辑");
            focusNode.recycle();
            return false;
        }
        
        // 使用剪贴板方式输入
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR2) {
            // 将文本放入剪贴板
            android.content.ClipboardManager clipboard = 
                (android.content.ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
            android.content.ClipData clip = android.content.ClipData.newPlainText("text", text);
            clipboard.setPrimaryClip(clip);
            
            // 粘贴
            focusNode.performAction(AccessibilityNodeInfo.ACTION_PASTE);
            Log.i(TAG, "通过剪贴板输入文本: " + text);
        } else {
            // 低版本使用ACTION_SET_TEXT
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                android.os.Bundle arguments = new android.os.Bundle();
                arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
                focusNode.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);
                Log.i(TAG, "通过SET_TEXT输入文本: " + text);
            }
        }
        
        focusNode.recycle();
        return true;
    }
    
    /**
     * 获取屏幕尺寸
     */
    public int[] getScreenSize() {
        Rect rect = new Rect();
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode != null) {
            rootNode.getBoundsInScreen(rect);
            rootNode.recycle();
        }
        return new int[]{rect.width(), rect.height()};
    }
    
    /**
     * 返回
     */
    public boolean goBack() {
        return performGlobalAction(GLOBAL_ACTION_BACK);
    }
    
    /**
     * 返回桌面
     */
    public boolean goHome() {
        return performGlobalAction(GLOBAL_ACTION_HOME);
    }
    
    /**
     * 打开最近任务
     */
    public boolean openRecents() {
        return performGlobalAction(GLOBAL_ACTION_RECENTS);
    }
    
    /**
     * 打开通知栏
     */
    public boolean openNotifications() {
        return performGlobalAction(GLOBAL_ACTION_NOTIFICATIONS);
    }
    
    /**
     * 打开快捷设置
     */
    public boolean openQuickSettings() {
        return performGlobalAction(GLOBAL_ACTION_QUICK_SETTINGS);
    }
}
