package com.zqautomation.floatwindow;

import android.annotation.SuppressLint;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;

import com.zqautomation.R;

/**
 * 悬浮窗服务 - 实现可拖动的悬浮控制按钮
 */
public class FloatWindowService extends Service {
    private static final String TAG = "FloatWindowService";
    
    private WindowManager windowManager;
    private WindowManager.LayoutParams params;
    private View floatView;
    private Button floatButton;
    
    private int lastX, lastY;
    private int initialX, initialY;
    private float initialTouchX, initialTouchY;
    private boolean isMoved = false;
    
    private FloatWindowCallback callback;
    
    public interface FloatWindowCallback {
        void onButtonClicked();
        void onButtonLongClicked();
    }
    
    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "悬浮窗服务创建");
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        showFloatWindow();
        return START_STICKY;
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        hideFloatWindow();
        Log.i(TAG, "悬浮窗服务销毁");
    }
    
    /**
     * 设置回调
     */
    public void setCallback(FloatWindowCallback callback) {
        this.callback = callback;
    }
    
    /**
     * 显示悬浮窗
     */
    @SuppressLint("ClickableViewAccessibility")
    private void showFloatWindow() {
        if (floatView != null) {
            return;
        }
        
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        
        // 创建悬浮窗布局参数
        params = new WindowManager.LayoutParams();
        params.type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O 
            ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY 
            : WindowManager.LayoutParams.TYPE_PHONE;
        params.format = PixelFormat.TRANSLUCENT;
        params.flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE 
            | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS;
        params.gravity = Gravity.TOP | Gravity.LEFT;
        params.width = WindowManager.LayoutParams.WRAP_CONTENT;
        params.height = WindowManager.LayoutParams.WRAP_CONTENT;
        params.x = 0;
        params.y = 200;
        
        // 创建悬浮窗视图
        floatView = createFloatView();
        
        // 添加触摸监听
        floatView.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        initialX = params.x;
                        initialY = params.y;
                        initialTouchX = event.getRawX();
                        initialTouchY = event.getRawY();
                        lastX = (int) event.getRawX();
                        lastY = (int) event.getRawY();
                        isMoved = false;
                        return true;
                        
                    case MotionEvent.ACTION_MOVE:
                        int dx = (int) (event.getRawX() - lastX);
                        int dy = (int) (event.getRawY() - lastY);
                        
                        if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                            isMoved = true;
                        }
                        
                        params.x += dx;
                        params.y += dy;
                        windowManager.updateViewLayout(floatView, params);
                        
                        lastX = (int) event.getRawX();
                        lastY = (int) event.getRawY();
                        return true;
                        
                    case MotionEvent.ACTION_UP:
                        if (!isMoved) {
                            // 单击
                            if (callback != null) {
                                callback.onButtonClicked();
                            }
                        }
                        return true;
                        
                    case MotionEvent.ACTION_CANCEL:
                        return false;
                }
                return false;
            }
        });
        
        // 长按监听
        floatView.setOnLongClickListener(new View.OnLongClickListener() {
            @Override
            public boolean onLongClick(View v) {
                if (callback != null) {
                    callback.onButtonLongClicked();
                }
                return true;
            }
        });
        
        // 添加到窗口
        try {
            windowManager.addView(floatView, params);
            Log.i(TAG, "悬浮窗已显示");
        } catch (Exception e) {
            Log.e(TAG, "显示悬浮窗失败", e);
        }
    }
    
    /**
     * 创建悬浮窗视图
     */
    private View createFloatView() {
        // 创建圆形按钮
        floatButton = new Button(this);
        floatButton.setText("ZQ");
        floatButton.setTextSize(12);
        floatButton.setTextColor(0xFFFFFFFF);
        floatButton.setBackgroundResource(android.R.drawable.btn_default);
        
        // 设置圆形背景
        floatButton.setBackground(createCircleBackground());
        
        // 设置大小 (25dp)
        int size = (int) (25 * getResources().getDisplayMetrics().density);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(size, size);
        floatButton.setLayoutParams(lp);
        
        // 设置内边距
        int padding = (int) (4 * getResources().getDisplayMetrics().density);
        floatButton.setPadding(padding, padding, padding, padding);
        
        return floatButton;
    }
    
    /**
     * 创建圆形背景
     */
    private android.graphics.drawable.Drawable createCircleBackground() {
        android.graphics.drawable.GradientDrawable shape = new android.graphics.drawable.GradientDrawable();
        shape.setShape(android.graphics.drawable.GradientDrawable.OVAL);
        shape.setColor(0xFF4CAF50); // 绿色
        shape.setStroke(2, 0xFFFFFFFF);
        return shape;
    }
    
    /**
     * 隐藏悬浮窗
     */
    public void hideFloatWindow() {
        if (floatView != null && windowManager != null) {
            try {
                windowManager.removeView(floatView);
            } catch (Exception e) {
                Log.e(TAG, "移除悬浮窗失败", e);
            }
            floatView = null;
        }
    }
    
    /**
     * 更新按钮文字
     */
    public void updateButtonText(String text) {
        if (floatButton != null) {
            floatButton.setText(text);
        }
    }
    
    /**
     * 更新按钮颜色
     */
    public void updateButtonColor(int color) {
        if (floatButton != null) {
            android.graphics.drawable.GradientDrawable shape = new android.graphics.drawable.GradientDrawable();
            shape.setShape(android.graphics.drawable.GradientDrawable.OVAL);
            shape.setColor(color);
            shape.setStroke(2, 0xFFFFFFFF);
            floatButton.setBackground(shape);
        }
    }
}
