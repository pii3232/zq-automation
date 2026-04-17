package com.zqautomation.accessibility;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.WindowManager;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;

/**
 * 截图辅助类 - 使用MediaProjection API实现屏幕截图
 */
public class ScreenshotHelper {
    private static final String TAG = "ScreenshotHelper";
    
    private Context context;
    private MediaProjectionManager projectionManager;
    private MediaProjection mediaProjection;
    private VirtualDisplay virtualDisplay;
    private ImageReader imageReader;
    private int screenWidth;
    private int screenHeight;
    private int screenDensity;
    private int resultCode;
    private Intent data;
    
    public ScreenshotHelper(Context context) {
        this.context = context;
        this.projectionManager = (MediaProjectionManager) 
            context.getSystemService(Context.MEDIA_PROJECTION_SERVICE);
        
        WindowManager windowManager = (WindowManager) 
            context.getSystemService(Context.WINDOW_SERVICE);
        DisplayMetrics metrics = new DisplayMetrics();
        windowManager.getDefaultDisplay().getMetrics(metrics);
        this.screenWidth = metrics.widthPixels;
        this.screenHeight = metrics.heightPixels;
        this.screenDensity = metrics.densityDpi;
    }
    
    /**
     * 设置投影权限数据
     */
    public void setProjectionData(int resultCode, Intent data) {
        this.resultCode = resultCode;
        this.data = data;
    }
    
    /**
     * 初始化MediaProjection
     */
    public boolean initProjection() {
        if (projectionManager == null) {
            Log.e(TAG, "MediaProjectionManager不可用");
            return false;
        }
        
        if (resultCode == 0 || data == null) {
            Log.e(TAG, "投影权限数据无效");
            return false;
        }
        
        mediaProjection = projectionManager.getMediaProjection(resultCode, data);
        if (mediaProjection == null) {
            Log.e(TAG, "创建MediaProjection失败");
            return false;
        }
        
        Log.i(TAG, "MediaProjection初始化成功");
        return true;
    }
    
    /**
     * 截取屏幕
     */
    public Bitmap takeScreenshot() {
        if (mediaProjection == null) {
            if (!initProjection()) {
                Log.e(TAG, "MediaProjection未初始化");
                return null;
            }
        }
        
        // 创建ImageReader
        imageReader = ImageReader.newInstance(
            screenWidth, screenHeight, 
            PixelFormat.RGBA_8888, 2
        );
        
        // 创建VirtualDisplay
        virtualDisplay = mediaProjection.createVirtualDisplay(
            "ScreenshotDisplay",
            screenWidth, screenHeight, screenDensity,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader.getSurface(), null, null
        );
        
        // 等待图像可用
        final Bitmap[] result = {null};
        final Object lock = new Object();
        
        ImageReader.OnImageAvailableListener listener = new ImageReader.OnImageAvailableListener() {
            @Override
            public void onImageAvailable(ImageReader reader) {
                Image image = null;
                try {
                    image = reader.acquireLatestImage();
                    if (image != null) {
                        Image.Plane[] planes = image.getPlanes();
                        ByteBuffer buffer = planes[0].getBuffer();
                        int pixelStride = planes[0].getPixelStride();
                        int rowStride = planes[0].getRowStride();
                        int rowPadding = rowStride - pixelStride * screenWidth;
                        
                        // 创建Bitmap
                        Bitmap bitmap = Bitmap.createBitmap(
                            screenWidth + rowPadding / pixelStride,
                            screenHeight,
                            Bitmap.Config.ARGB_8888
                        );
                        bitmap.copyPixelsFromBuffer(buffer);
                        
                        // 裁剪到正确尺寸
                        result[0] = Bitmap.createBitmap(
                            bitmap, 0, 0, screenWidth, screenHeight
                        );
                        bitmap.recycle();
                        
                        synchronized (lock) {
                            lock.notify();
                        }
                    }
                } catch (Exception e) {
                    Log.e(TAG, "截图失败", e);
                } finally {
                    if (image != null) {
                        image.close();
                    }
                }
            }
        };
        
        imageReader.setOnImageAvailableListener(listener, new Handler(Looper.getMainLooper()));
        
        // 等待截图完成
        synchronized (lock) {
            try {
                lock.wait(3000);
            } catch (InterruptedException e) {
                Log.e(TAG, "截图等待被中断", e);
            }
        }
        
        // 清理资源
        if (virtualDisplay != null) {
            virtualDisplay.release();
            virtualDisplay = null;
        }
        
        return result[0];
    }
    
    /**
     * 截图并保存到文件
     */
    public String takeScreenshotAndSave(String filename) {
        Bitmap bitmap = takeScreenshot();
        if (bitmap == null) {
            return null;
        }
        
        try {
            File file = new File(filename);
            File parent = file.getParentFile();
            if (parent != null && !parent.exists()) {
                parent.mkdirs();
            }
            
            FileOutputStream fos = new FileOutputStream(file);
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, fos);
            fos.flush();
            fos.close();
            
            Log.i(TAG, "截图已保存: " + filename);
            return filename;
        } catch (Exception e) {
            Log.e(TAG, "保存截图失败", e);
            return null;
        } finally {
            bitmap.recycle();
        }
    }
    
    /**
     * 释放资源
     */
    public void release() {
        if (virtualDisplay != null) {
            virtualDisplay.release();
            virtualDisplay = null;
        }
        
        if (imageReader != null) {
            imageReader.setOnImageAvailableListener(null, null);
            imageReader = null;
        }
        
        if (mediaProjection != null) {
            mediaProjection.stop();
            mediaProjection = null;
        }
        
        Log.i(TAG, "ScreenshotHelper资源已释放");
    }
}
