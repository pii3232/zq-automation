import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * 找图算法测试工具类 - 纯Java版本（不依赖OpenCV）
 * 
 * 此类展示找图算法的接口设计和逻辑
 * 实际使用时需要集成OpenCV库
 * 
 * OpenCV集成方式：
 * 1. 下载OpenCV Java版本：https://opencv.org/releases/
 * 2. 解压后找到 opencv-javaxxx.jar 和对应的native库
 * 3. 添加jar到项目依赖
 * 4. 加载native库：System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
 * 
 * Android项目：
 * 1. 在build.gradle中添加：implementation 'org.opencv:opencv:4.5.5'
 * 2. 或使用OpenCV Manager APK
 */
public class ImageMatchTest {
    
    /**
     * 找图算法枚举
     */
    public enum MatchMethod {
        /**
         * 归一化相关系数匹配（推荐）
         * 返回值范围：-1 到 1，值越大越匹配
         * 相似度 = 匹配值
         */
        TM_CCOEFF_NORMED(0, "TM_CCOEFF_NORMED (推荐)", true),
        
        /**
         * 归一化相关匹配
         * 返回值范围：0 到 1，值越大越匹配
         * 相似度 = 匹配值
         */
        TM_CCORR_NORMED(1, "TM_CCORR_NORMED", true),
        
        /**
         * 归一化平方差匹配
         * 返回值范围：0 到 1，值越小越匹配
         * 相似度 = 1 - 匹配值
         */
        TM_SQDIFF_NORMED(2, "TM_SQDIFF_NORMED", true),
        
        /**
         * 相关系数匹配（非归一化）
         * 返回值范围不确定，值越大越匹配
         * 无法直接计算相似度
         */
        TM_CCOEFF(3, "TM_CCOEFF", false),
        
        /**
         * 相关匹配（非归一化）
         * 返回值范围不确定，值越大越匹配
         * 无法直接计算相似度
         */
        TM_CCORR(4, "TM_CCORR", false),
        
        /**
         * 平方差匹配（非归一化）
         * 返回值范围不确定，值越小越匹配
         * 无法直接计算相似度
         */
        TM_SQDIFF(5, "TM_SQDIFF", false);
        
        private final int index;
        private final String displayName;
        private final boolean isNormalized;
        
        MatchMethod(int index, String displayName, boolean isNormalized) {
            this.index = index;
            this.displayName = displayName;
            this.isNormalized = isNormalized;
        }
        
        public int getIndex() { return index; }
        public String getDisplayName() { return displayName; }
        public boolean isNormalized() { return isNormalized; }
        
        public static MatchMethod fromIndex(int index) {
            for (MatchMethod method : values()) {
                if (method.index == index) return method;
            }
            return TM_CCOEFF_NORMED;
        }
    }
    
    /**
     * 找图结果
     */
    public static class MatchResult {
        public boolean found;           // 是否找到
        public int x;                   // X坐标
        public int y;                   // Y坐标
        public int width;               // 模板宽度
        public int height;              // 模板高度
        public double similarity;       // 相似度（归一化算法0-1）
        public double matchValue;       // 原始匹配值
        public long elapsedTimeMs;      // 耗时（毫秒）
        public MatchMethod method;      // 使用的算法
        public String message;          // 结果消息
        public String errorMessage;     // 错误信息
        
        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            sb.append("算法: ").append(method.getDisplayName()).append("\n");
            sb.append("结果: ").append(found ? "找到匹配" : "未找到").append("\n");
            sb.append("坐标: (").append(x).append(", ").append(y).append(")\n");
            sb.append("尺寸: ").append(width).append("x").append(height).append("\n");
            
            if (method.isNormalized()) {
                sb.append("相似度: ").append(String.format("%.4f", similarity)).append("\n");
            } else {
                sb.append("匹配值: ").append(String.format("%.2f", matchValue)).append(" (非归一化)\n");
            }
            
            sb.append("耗时: ").append(elapsedTimeMs).append("ms");
            
            return sb.toString();
        }
    }
    
    /**
     * 多算法测试结果
     */
    public static class MultiTestResult {
        public List<MatchResult> results = new ArrayList<>();
        public String sourceImagePath;
        public String templateImagePath;
        public int sourceWidth;
        public int sourceHeight;
        
        public void addResult(MatchResult result) {
            results.add(result);
        }
        
        public MatchResult getBestResult() {
            if (results.isEmpty()) return null;
            
            MatchResult best = null;
            for (MatchResult r : results) {
                if (r.found) {
                    if (best == null || r.similarity > best.similarity) {
                        best = r;
                    }
                }
            }
            return best;
        }
    }
    
    // ==================== OpenCV接口（需要OpenCV库） ====================
    
    /**
     * 使用OpenCV执行模板匹配
     * 
     * 需要先加载OpenCV库：
     * System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
     * 
     * @param sourceImage 源图像（OpenCV Mat对象）
     * @param templateImage 模板图像（OpenCV Mat对象）
     * @param method 找图算法
     * @param threshold 相似度阈值（默认0.8）
     * @return 匹配结果
     */
    /*
    public static MatchResult matchTemplate(Mat sourceImage, Mat templateImage, 
                                           MatchMethod method, double threshold) {
        MatchResult result = new MatchResult();
        result.method = method;
        
        if (sourceImage == null || sourceImage.empty()) {
            result.found = false;
            result.errorMessage = "源图像为空";
            return result;
        }
        
        if (templateImage == null || templateImage.empty()) {
            result.found = false;
            result.errorMessage = "模板图像为空";
            return result;
        }
        
        // 检查模板是否大于源图像
        if (templateImage.cols() > sourceImage.cols() || 
            templateImage.rows() > sourceImage.rows()) {
            result.found = false;
            result.errorMessage = "模板图像大于源图像";
            return result;
        }
        
        try {
            long startTime = System.currentTimeMillis();
            
            // 创建结果矩阵
            Mat resultMat = new Mat();
            
            // 获取OpenCV方法常量
            int opencvMethod = getOpenCVMethod(method);
            
            // 执行模板匹配
            Imgproc.matchTemplate(sourceImage, templateImage, resultMat, opencvMethod);
            
            // 查找最佳匹配位置
            Core.MinMaxLocResult minMaxResult = Core.minMaxLoc(resultMat);
            
            result.elapsedTimeMs = System.currentTimeMillis() - startTime;
            
            // 获取模板尺寸
            result.width = templateImage.cols();
            result.height = templateImage.rows();
            
            // 根据算法类型处理结果
            processResult(result, minMaxResult, opencvMethod, threshold);
            
            resultMat.release();
            
        } catch (Exception e) {
            result.found = false;
            result.errorMessage = "错误: " + e.getMessage();
        }
        
        return result;
    }
    */
    
    /**
     * 获取OpenCV方法常量
     */
    /*
    private static int getOpenCVMethod(MatchMethod method) {
        switch (method) {
            case TM_CCOEFF_NORMED: return Imgproc.TM_CCOEFF_NORMED;
            case TM_CCORR_NORMED: return Imgproc.TM_CCORR_NORMED;
            case TM_SQDIFF_NORMED: return Imgproc.TM_SQDIFF_NORMED;
            case TM_CCOEFF: return Imgproc.TM_CCOEFF;
            case TM_CCORR: return Imgproc.TM_CCORR;
            case TM_SQDIFF: return Imgproc.TM_SQDIFF;
            default: return Imgproc.TM_CCOEFF_NORMED;
        }
    }
    */
    
    /**
     * 处理匹配结果
     */
    /*
    private static void processResult(MatchResult result, Core.MinMaxLocResult minMaxResult,
                                     int opencvMethod, double threshold) {
        // SQDIFF方法：值越小越好
        if (opencvMethod == Imgproc.TM_SQDIFF || opencvMethod == Imgproc.TM_SQDIFF_NORMED) {
            result.matchValue = minMaxResult.minVal;
            result.x = (int) minMaxResult.minLoc.x;
            result.y = (int) minMaxResult.minLoc.y;
            
            if (result.method.isNormalized()) {
                result.similarity = 1.0 - result.matchValue;
            } else {
                result.similarity = -1;
            }
        } else {
            // 其他方法：值越大越好
            result.matchValue = minMaxResult.maxVal;
            result.x = (int) minMaxResult.maxLoc.x;
            result.y = (int) minMaxResult.maxLoc.y;
            
            if (result.method.isNormalized()) {
                result.similarity = result.matchValue;
            } else {
                result.similarity = -1;
            }
        }
        
        // 判断是否找到匹配
        if (result.method.isNormalized()) {
            result.found = result.similarity >= threshold;
            if (result.found) {
                result.message = String.format("找到匹配! 相似度: %.4f", result.similarity);
            } else {
                result.message = String.format("未找到匹配. 相似度: %.4f < %.2f", 
                        result.similarity, threshold);
            }
        } else {
            result.found = true;
            result.message = String.format("最佳匹配! 匹配值: %.2f (非归一化算法)", 
                    result.matchValue);
        }
    }
    */
    
    // ==================== 测试和演示 ====================
    
    /**
     * 打印算法说明
     */
    public static void printAlgorithmInfo() {
        System.out.println("========================================");
        System.out.println("OpenCV模板匹配算法说明");
        System.out.println("========================================");
        
        for (MatchMethod method : MatchMethod.values()) {
            System.out.println("\n" + method.getDisplayName());
            System.out.println("  归一化: " + (method.isNormalized() ? "是" : "否"));
            
            switch (method) {
                case TM_CCOEFF_NORMED:
                    System.out.println("  说明: 归一化相关系数匹配，推荐使用");
                    System.out.println("  返回值: -1到1，值越大越匹配");
                    System.out.println("  相似度: 直接使用匹配值");
                    break;
                case TM_CCORR_NORMED:
                    System.out.println("  说明: 归一化相关匹配");
                    System.out.println("  返回值: 0到1，值越大越匹配");
                    System.out.println("  相似度: 直接使用匹配值");
                    break;
                case TM_SQDIFF_NORMED:
                    System.out.println("  说明: 归一化平方差匹配");
                    System.out.println("  返回值: 0到1，值越小越匹配");
                    System.out.println("  相似度: 1 - 匹配值");
                    break;
                case TM_CCOEFF:
                    System.out.println("  说明: 相关系数匹配（非归一化）");
                    System.out.println("  返回值: 范围不确定，值越大越匹配");
                    System.out.println("  注意: 无法直接计算相似度");
                    break;
                case TM_CCORR:
                    System.out.println("  说明: 相关匹配（非归一化）");
                    System.out.println("  返回值: 范围不确定，值越大越匹配");
                    System.out.println("  注意: 无法直接计算相似度");
                    break;
                case TM_SQDIFF:
                    System.out.println("  说明: 平方差匹配（非归一化）");
                    System.out.println("  返回值: 范围不确定，值越小越匹配");
                    System.out.println("  注意: 无法直接计算相似度");
                    break;
            }
        }
        
        System.out.println("\n========================================");
        System.out.println("推荐使用: TM_CCOEFF_NORMED");
        System.out.println("原因: 对亮度变化不敏感，返回值可直接作为相似度");
        System.out.println("========================================");
    }
    
    /**
     * 演示结果格式
     */
    public static void demoResultFormat() {
        System.out.println("\n========== 结果格式演示 ==========\n");
        
        // 模拟归一化算法找到匹配
        MatchResult result1 = new MatchResult();
        result1.found = true;
        result1.x = 1613;
        result1.y = 961;
        result1.width = 50;
        result1.height = 30;
        result1.similarity = 0.9523;
        result1.matchValue = 0.9523;
        result1.elapsedTimeMs = 240;
        result1.method = MatchMethod.TM_CCOEFF_NORMED;
        
        System.out.println("【归一化算法 - 找到匹配】");
        System.out.println(result1.toString());
        
        // 模拟归一化算法未找到匹配
        MatchResult result2 = new MatchResult();
        result2.found = false;
        result2.x = 100;
        result2.y = 200;
        result2.width = 50;
        result2.height = 30;
        result2.similarity = 0.5999;
        result2.matchValue = 0.5999;
        result2.elapsedTimeMs = 235;
        result2.method = MatchMethod.TM_CCOEFF_NORMED;
        
        System.out.println("\n【归一化算法 - 未找到匹配】");
        System.out.println(result2.toString());
        
        // 模拟非归一化算法
        MatchResult result3 = new MatchResult();
        result3.found = true;
        result3.x = 1613;
        result3.y = 961;
        result3.width = 50;
        result3.height = 30;
        result3.similarity = -1;
        result3.matchValue = 52400436.0;
        result3.elapsedTimeMs = 180;
        result3.method = MatchMethod.TM_CCOEFF;
        
        System.out.println("\n【非归一化算法】");
        System.out.println(result3.toString());
    }
    
    /**
     * 主函数
     */
    public static void main(String[] args) {
        System.out.println("找图算法测试工具 (Java版本)");
        System.out.println("需要OpenCV库才能执行实际匹配\n");
        
        // 打印算法说明
        printAlgorithmInfo();
        
        // 演示结果格式
        demoResultFormat();
        
        System.out.println("\n========== 使用说明 ==========");
        System.out.println("1. 下载OpenCV Java版本: https://opencv.org/releases/");
        System.out.println("2. 添加opencv-java.jar到项目依赖");
        System.out.println("3. 加载native库: System.loadLibrary(Core.NATIVE_LIBRARY_NAME)");
        System.out.println("4. 调用matchTemplate()方法执行匹配");
        System.out.println("\nAndroid项目:");
        System.out.println("在build.gradle添加: implementation 'org.opencv:opencv:4.5.5'");
        System.out.println("或参考: ImageMatchTestActivity.java");
    }
}
