import javax.swing.*;
import javax.swing.border.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.*;
import java.io.*;
import javax.imageio.*;
import java.util.*;
import java.text.*;

/**
 * 找图算法测试工具 - Java Swing GUI版本
 * 功能与SJJM.PY完全一致
 * 
 * 编译: javac -encoding UTF-8 ImageMatchTestGUI.java
 * 运行: java ImageMatchTestGUI
 * 
 * 如需OpenCV支持:
 * 编译: javac -encoding UTF-8 -cp opencv-xxx.jar ImageMatchTestGUI.java
 * 运行: java -Djava.library.path=opencv_native -cp .;opencv-xxx.jar ImageMatchTestGUI
 */
public class ImageMatchTestGUI extends JFrame {
    
    // 找图算法枚举
    public enum MatchMethod {
        TM_CCOEFF_NORMED(0, "TM_CCOEFF_NORMED (推荐)", true),
        TM_CCORR_NORMED(1, "TM_CCORR_NORMED", true),
        TM_SQDIFF_NORMED(2, "TM_SQDIFF_NORMED", true),
        TM_CCOEFF(3, "TM_CCOEFF", false),
        TM_CCORR(4, "TM_CCORR", false),
        TM_SQDIFF(5, "TM_SQDIFF", false);
        
        private final int index;
        private final String displayName;
        private final boolean isNormalized;
        
        MatchMethod(int index, String displayName, boolean isNormalized) {
            this.index = index;
            this.displayName = displayName;
            this.isNormalized = isNormalized;
        }
        
        public String getDisplayName() { return displayName; }
        public boolean isNormalized() { return isNormalized; }
        
        public static MatchMethod fromIndex(int idx) {
            for (MatchMethod m : values()) if (m.index == idx) return m;
            return TM_CCOEFF_NORMED;
        }
    }
    
    // 找图结果类
    public static class MatchResult {
        public boolean found;
        public int x, y, width, height;
        public double similarity, matchValue;
        public long elapsedTimeMs;
        public MatchMethod method;
    }
    
    // 选择回调接口
    public interface SelectionCallback { void onSelectionFinished(int x, int y, int w, int h); }
    
    // 图像显示面板（支持框选和测试结果显示）
    public class ImageDisplayPanel extends JPanel {
        private BufferedImage currentImage;
        private boolean screenshotMode = false;
        private Point startPoint, endPoint;
        private boolean isSelecting = false;
        private java.util.List<int[]> testResults = new ArrayList<>();
        private SelectionCallback selectionCallback;
        
        public ImageDisplayPanel() {
            setPreferredSize(new Dimension(2248, 1080));
            setBackground(new Color(30, 30, 30));
            MyMouseAdapter ma = new MyMouseAdapter();
            addMouseListener(ma);
            addMouseMotionListener(ma);
        }
        
        public void setImage(BufferedImage img) {
            this.currentImage = img;
            if (img != null) setPreferredSize(new Dimension(img.getWidth(), img.getHeight()));
            repaint();
        }
        
        public BufferedImage getImage() { return currentImage; }
        
        public void startScreenshotMode() {
            screenshotMode = true; startPoint = null; endPoint = null; isSelecting = false;
            setCursor(Cursor.getPredefinedCursor(Cursor.CROSSHAIR_CURSOR));
            repaint();
        }
        
        public void stopScreenshotMode() {
            screenshotMode = false; startPoint = null; endPoint = null; isSelecting = false;
            setCursor(Cursor.getDefaultCursor());
            repaint();
        }
        
        public void setTestResult(int x, int y, int w, int h, double sim) {
            testResults.clear();
            testResults.add(new int[]{x, y, w, h, (int)(sim * 100)});
            repaint();
        }
        
        public void clearTestResults() { testResults.clear(); repaint(); }
        
        public void setSelectionCallback(SelectionCallback cb) { this.selectionCallback = cb; }
        
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            
            if (currentImage != null) {
                g2d.drawImage(currentImage, 0, 0, null);
            } else {
                g2d.setColor(Color.GRAY);
                g2d.setFont(new Font("微软雅黑", Font.PLAIN, 24));
                String text = "请先连接设备并开始投影";
                FontMetrics fm = g2d.getFontMetrics();
                g2d.drawString(text, (getWidth() - fm.stringWidth(text)) / 2, getHeight() / 2);
            }
            
            // 绘制测试结果（绿色框）
            for (int[] r : testResults) {
                g2d.setColor(Color.GREEN);
                g2d.setStroke(new BasicStroke(3));
                g2d.drawRect(r[0], r[1], r[2], r[3]);
                g2d.setFont(new Font("微软雅黑", Font.BOLD, 14));
                g2d.drawString(String.format("(%d,%d) %.2f", r[0], r[1], r[4] / 100.0), r[0] + 5, r[1] - 5);
            }
            
            // 绘制框选区域（红色边框）
            if (screenshotMode && startPoint != null && endPoint != null) {
                int x = Math.min(startPoint.x, endPoint.x);
                int y = Math.min(startPoint.y, endPoint.y);
                int w = Math.abs(endPoint.x - startPoint.x);
                int h = Math.abs(endPoint.y - startPoint.y);
                g2d.setColor(Color.RED);
                g2d.setStroke(new BasicStroke(2));
                g2d.drawRect(x, y, w, h);
                g2d.setColor(Color.WHITE);
                g2d.setFont(new Font("微软雅黑", Font.BOLD, 12));
                g2d.drawString(String.format("%d x %d", w, h), x + 5, y + 18);
            }
        }
        
        private class MyMouseAdapter extends MouseAdapter {
            public void mousePressed(MouseEvent e) {
                if (screenshotMode && SwingUtilities.isLeftMouseButton(e)) {
                    startPoint = e.getPoint(); endPoint = e.getPoint(); isSelecting = true;
                    repaint();
                }
            }
            public void mouseDragged(MouseEvent e) {
                if (screenshotMode && isSelecting) { endPoint = e.getPoint(); repaint(); }
            }
            public void mouseReleased(MouseEvent e) {
                if (screenshotMode && SwingUtilities.isLeftMouseButton(e) && isSelecting) {
                    isSelecting = false;
                    if (startPoint != null && endPoint != null) {
                        int x = Math.min(startPoint.x, endPoint.x);
                        int y = Math.min(startPoint.y, endPoint.y);
                        int w = Math.abs(endPoint.x - startPoint.x);
                        int h = Math.abs(endPoint.y - startPoint.y);
                        if (w > 5 && h > 5 && selectionCallback != null) {
                            selectionCallback.onSelectionFinished(x, y, w, h);
                            return;
                        }
                    }
                    stopScreenshotMode();
                }
            }
        }
    }
    
    // 主界面组件
    private JTextField ipField, portField, fpsField, testImagePathField, thresholdField;
    private JButton btnConnect, btnDisconnect, btnStartProjection, btnStopProjection;
    private JButton btnBrowseImage, btnTestFind, btnClearTest, btnScreenshot;
    private JLabel lblStatus, lblTestResult, lblSavePath, screenshotPreview, lblCoord;
    private JComboBox<String> algoComboBox;
    private JTextArea logArea;
    private ImageDisplayPanel imageDisplayPanel;
    
    // 状态
    private boolean connected = false, projectionRunning = false;
    private String deviceIp = "192.168.3.21", devicePort = "5555";
    private String picDirectory = "E:\\5-ZDZS-TXA5\\3MCWB\\pic";
    private Thread projectionThread;
    
    public ImageMatchTestGUI() {
        initUI();
    }
    
    private void initUI() {
        setTitle("手机镜像 - 找图测试工具 (Java Swing)");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        JPanel mainPanel = new JPanel(new BorderLayout(5, 5));
        mainPanel.setBorder(new EmptyBorder(5, 5, 5, 5));
        
        // 左侧面板
        JPanel leftPanel = createLeftPanel();
        leftPanel.setPreferredSize(new Dimension(450, 1080));
        mainPanel.add(leftPanel, BorderLayout.WEST);
        
        // 右侧面板
        JPanel rightPanel = createRightPanel();
        mainPanel.add(rightPanel, BorderLayout.CENTER);
        
        setContentPane(mainPanel);
        setSize(2750, 1150);
        setLocationRelativeTo(null);
        
        // ESC取消截图
        getRootPane().registerKeyboardAction(e -> {
            if (imageDisplayPanel.screenshotMode) {
                imageDisplayPanel.stopScreenshotMode();
                log("已取消截图");
            }
        }, KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), JComponent.WHEN_IN_FOCUSED_WINDOW);
    }
    
    private JPanel createLeftPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        
        // 设备连接
        JPanel g1 = createGroup("设备连接");
        JPanel c1 = new JPanel(); c1.setLayout(new BoxLayout(c1, BoxLayout.Y_AXIS));
        
        JPanel p1 = new JPanel(new FlowLayout(FlowLayout.LEFT)); p1.add(new JLabel("IP地址:"));
        ipField = new JTextField(deviceIp, 15); p1.add(ipField); c1.add(p1);
        
        JPanel p2 = new JPanel(new FlowLayout(FlowLayout.LEFT)); p2.add(new JLabel("端口:"));
        portField = new JTextField(devicePort, 10); p2.add(portField); c1.add(p2);
        
        JPanel p3 = new JPanel(new FlowLayout(FlowLayout.LEFT));
        btnConnect = new JButton("连接设备"); btnConnect.addActionListener(e -> connectDevice()); p3.add(btnConnect);
        btnDisconnect = new JButton("断开连接"); btnDisconnect.setEnabled(false);
        btnDisconnect.addActionListener(e -> disconnectDevice()); p3.add(btnDisconnect); c1.add(p3);
        
        lblStatus = new JLabel("状态: 未连接"); lblStatus.setForeground(Color.RED); c1.add(lblStatus);
        g1.add(c1, BorderLayout.CENTER); panel.add(g1);
        
        // 投影控制
        JPanel g2 = createGroup("投影控制");
        JPanel c2 = new JPanel(); c2.setLayout(new BoxLayout(c2, BoxLayout.Y_AXIS));
        
        JPanel p4 = new JPanel(new FlowLayout(FlowLayout.LEFT));
        btnStartProjection = new JButton("开始投影"); btnStartProjection.setPreferredSize(new Dimension(120, 30));
        btnStartProjection.setEnabled(false); btnStartProjection.addActionListener(e -> startProjection()); p4.add(btnStartProjection);
        btnStopProjection = new JButton("停止投影"); btnStopProjection.setPreferredSize(new Dimension(120, 30));
        btnStopProjection.setEnabled(false); btnStopProjection.addActionListener(e -> stopProjection()); p4.add(btnStopProjection); c2.add(p4);
        
        JPanel p5 = new JPanel(new FlowLayout(FlowLayout.LEFT)); p5.add(new JLabel("刷新间隔(ms):"));
        fpsField = new JTextField("200", 5); p5.add(fpsField); c2.add(p5);
        g2.add(c2, BorderLayout.CENTER); panel.add(g2);
        
        // 测试区
        JPanel g3 = createGroup("测试区");
        JPanel c3 = new JPanel(); c3.setLayout(new BoxLayout(c3, BoxLayout.Y_AXIS));
        
        JPanel p6 = new JPanel(new BorderLayout(5, 0)); p6.add(new JLabel("图片路径:"), BorderLayout.WEST);
        testImagePathField = new JTextField(); p6.add(testImagePathField, BorderLayout.CENTER);
        btnBrowseImage = new JButton("浏览"); btnBrowseImage.addActionListener(e -> browseTestImage());
        p6.add(btnBrowseImage, BorderLayout.EAST); c3.add(p6);
        
        JPanel p7 = new JPanel(new FlowLayout(FlowLayout.LEFT)); p7.add(new JLabel("找图算法:"));
        algoComboBox = new JComboBox<>(new String[]{"TM_CCOEFF_NORMED (推荐)", "TM_CCORR_NORMED",
            "TM_SQDIFF_NORMED", "TM_CCOEFF", "TM_CCORR", "TM_SQDIFF"}); p7.add(algoComboBox); c3.add(p7);
        
        JPanel p8 = new JPanel(new FlowLayout(FlowLayout.LEFT)); p8.add(new JLabel("相似度阈值:"));
        thresholdField = new JTextField("0.8", 5); p8.add(thresholdField); c3.add(p8);
        
        JPanel p9 = new JPanel(new FlowLayout(FlowLayout.LEFT));
        btnTestFind = new JButton("测试找图"); btnTestFind.setPreferredSize(new Dimension(100, 30));
        btnTestFind.addActionListener(e -> testFindImage()); p9.add(btnTestFind);
        btnClearTest = new JButton("清除结果"); btnClearTest.setPreferredSize(new Dimension(100, 30));
        btnClearTest.addActionListener(e -> clearTestResults()); p9.add(btnClearTest); c3.add(p9);
        
        lblTestResult = new JLabel("测试结果: -"); lblTestResult.setForeground(new Color(0, 150, 0));
        lblTestResult.setPreferredSize(new Dimension(400, 60)); c3.add(lblTestResult);
        g3.add(c3, BorderLayout.CENTER); panel.add(g3);
        
        // 截图工具
        JPanel g4 = createGroup("截图工具");
        JPanel c4 = new JPanel(); c4.setLayout(new BoxLayout(c4, BoxLayout.Y_AXIS));
        
        btnScreenshot = new JButton("截图"); btnScreenshot.addActionListener(e -> takeScreenshot()); c4.add(btnScreenshot);
        lblSavePath = new JLabel("<html>保存目录:<br>" + picDirectory + "</html>"); c4.add(lblSavePath);
        
        screenshotPreview = new JLabel("暂无截图"); screenshotPreview.setPreferredSize(new Dimension(400, 150));
        screenshotPreview.setBackground(new Color(45, 45, 45)); screenshotPreview.setOpaque(true);
        screenshotPreview.setHorizontalAlignment(SwingConstants.CENTER);
        screenshotPreview.setBorder(BorderFactory.createLineBorder(Color.GRAY)); c4.add(screenshotPreview);
        g4.add(c4, BorderLayout.CENTER); panel.add(g4);
        
        // 日志
        JPanel g5 = createGroup("日志");
        logArea = new JTextArea(8, 30); logArea.setEditable(false);
        logArea.setFont(new Font("微软雅黑", Font.PLAIN, 12));
        g5.add(new JScrollPane(logArea), BorderLayout.CENTER); panel.add(g5);
        
        return panel;
    }
    
    private JPanel createRightPanel() {
        JPanel panel = new JPanel(new BorderLayout(5, 5));
        JPanel g = createGroup("设备屏幕投影 (2248x1080)");
        
        imageDisplayPanel = new ImageDisplayPanel();
        imageDisplayPanel.setSelectionCallback((x, y, w, h) -> {
            imageDisplayPanel.stopScreenshotMode();
            onSelectionFinished(x, y, w, h);
        });
        
        JScrollPane sp = new JScrollPane(imageDisplayPanel);
        sp.setPreferredSize(new Dimension(2260, 1100));
        g.add(sp, BorderLayout.CENTER);
        
        JPanel coordPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        lblCoord = new JLabel("坐标: (-, -)"); lblCoord.setForeground(Color.BLUE); coordPanel.add(lblCoord);
        g.add(coordPanel, BorderLayout.SOUTH);
        
        panel.add(g, BorderLayout.CENTER);
        
        imageDisplayPanel.addMouseMotionListener(new MouseAdapter() {
            public void mouseMoved(MouseEvent e) {
                if (!imageDisplayPanel.screenshotMode)
                    lblCoord.setText(String.format("坐标: (%d, %d)", e.getX(), e.getY()));
            }
        });
        
        return panel;
    }
    
    private JPanel createGroup(String title) {
        JPanel p = new JPanel(new BorderLayout());
        p.setBorder(BorderFactory.createTitledBorder(BorderFactory.createEtchedBorder(), title,
            TitledBorder.LEFT, TitledBorder.TOP, new Font("微软雅黑", Font.PLAIN, 12)));
        return p;
    }
    
    private void log(String msg) {
        String ts = new SimpleDateFormat("HH:mm:ss").format(new Date());
        logArea.append(String.format("[%s] %s\n", ts, msg));
        logArea.setCaretPosition(logArea.getDocument().getLength());
    }
    
    private void connectDevice() {
        String ip = ipField.getText().trim(), port = portField.getText().trim();
        if (ip.isEmpty()) { log("请输入IP地址"); return; }
        log("正在连接设备: " + ip + ":" + port);
        try {
            ProcessBuilder pb = new ProcessBuilder("adb", "connect", ip + ":" + port);
            pb.redirectErrorStream(true);
            Process p = pb.start();
            BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
            StringBuilder out = new StringBuilder();
            String line; while ((line = r.readLine()) != null) out.append(line);
            p.waitFor();
            
            if (out.toString().toLowerCase().contains("connected")) {
                connected = true; deviceIp = ip; devicePort = port;
                log("连接成功: " + out);
                lblStatus.setText("状态: 已连接 (" + ip + ":" + port + ")"); lblStatus.setForeground(new Color(0, 150, 0));
                btnConnect.setEnabled(false); btnDisconnect.setEnabled(true); btnStartProjection.setEnabled(true);
            } else log("连接失败: " + out);
        } catch (Exception e) { log("连接错误: " + e.getMessage()); }
    }
    
    private void disconnectDevice() {
        if (projectionRunning) stopProjection();
        try { new ProcessBuilder("adb", "disconnect", deviceIp + ":" + devicePort).start(); } catch (Exception e) {}
        connected = false;
        lblStatus.setText("状态: 未连接"); lblStatus.setForeground(Color.RED);
        btnConnect.setEnabled(true); btnDisconnect.setEnabled(false);
        btnStartProjection.setEnabled(false); btnStopProjection.setEnabled(false);
        imageDisplayPanel.setImage(null);
        log("设备已断开");
    }
    
    private void startProjection() {
        if (!connected) return;
        projectionRunning = true;
        btnStartProjection.setEnabled(false); btnStopProjection.setEnabled(true);
        log("开始投影...");
        
        projectionThread = new Thread(() -> {
            while (projectionRunning) {
                try {
                    int interval = Integer.parseInt(fpsField.getText().trim());
                    if (interval < 50) interval = 200;
                    long start = System.currentTimeMillis();
                    
                    ProcessBuilder pb = new ProcessBuilder("adb", "-s", deviceIp + ":" + devicePort,
                        "exec-out", "screencap", "-p");
                    pb.redirectErrorStream(false);
                    Process p = pb.start();
                    BufferedImage img = ImageIO.read(p.getInputStream());
                    p.waitFor();
                    
                    if (img != null) SwingUtilities.invokeLater(() -> imageDisplayPanel.setImage(img));
                    
                    long wait = Math.max(10, interval - (System.currentTimeMillis() - start));
                    Thread.sleep(wait);
                } catch (Exception e) {
                    if (projectionRunning) { log("投影错误: " + e.getMessage()); try { Thread.sleep(1000); } catch (Exception ex) {} }
                }
            }
        });
        projectionThread.setDaemon(true);
        projectionThread.start();
    }
    
    private void stopProjection() {
        projectionRunning = false;
        btnStartProjection.setEnabled(true); btnStopProjection.setEnabled(false);
        log("投影已停止");
    }
    
    private void browseTestImage() {
        JFileChooser fc = new JFileChooser(picDirectory);
        fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter("图片 (*.png, *.jpg, *.bmp)", "png", "jpg", "jpeg", "bmp"));
        if (fc.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
            testImagePathField.setText(fc.getSelectedFile().getAbsolutePath());
            log("已选择: " + fc.getSelectedFile().getName());
        }
    }
    
    private void testFindImage() {
        BufferedImage src = imageDisplayPanel.getImage();
        if (src == null) { log("当前没有设备画面，请先开始投影"); return; }
        
        String path = testImagePathField.getText().trim();
        if (path.isEmpty()) { log("请输入图片路径"); return; }
        
        File f = new File(path);
        if (!f.exists()) f = new File(picDirectory, path);
        if (!f.exists()) { log("图片不存在: " + path); return; }
        
        try {
            BufferedImage tpl = ImageIO.read(f);
            if (tpl == null) { log("无法读取图片"); return; }
            
            MatchMethod method = MatchMethod.fromIndex(algoComboBox.getSelectedIndex());
            double threshold = Double.parseDouble(thresholdField.getText().trim());
            
            long start = System.currentTimeMillis();
            MatchResult res = matchTemplate(src, tpl, method, threshold);
            res.elapsedTimeMs = System.currentTimeMillis() - start;
            
            if (res.found) {
                imageDisplayPanel.setTestResult(res.x, res.y, res.width, res.height, res.similarity);
                String txt = String.format("找到匹配! 坐标: (%d, %d), 尺寸: %dx%d, 相似度: %.4f, 耗时: %dms",
                    res.x, res.y, res.width, res.height, res.similarity, res.elapsedTimeMs);
                lblTestResult.setText("<html>" + txt + "</html>");
                lblTestResult.setForeground(new Color(0, 150, 0));
                log(txt);
            } else {
                imageDisplayPanel.clearTestResults();
                String txt = method.isNormalized() ?
                    String.format("未找到匹配. 最高相似度: %.4f < %.2f, 耗时: %dms", res.similarity, threshold, res.elapsedTimeMs) :
                    String.format("最佳匹配! 坐标: (%d, %d), 匹配值: %.2f, 耗时: %dms (非归一化)", res.x, res.y, res.matchValue, res.elapsedTimeMs);
                lblTestResult.setText("<html>" + txt + "</html>");
                lblTestResult.setForeground(method.isNormalized() ? Color.RED : Color.BLUE);
                log(txt);
            }
        } catch (Exception e) { log("测试错误: " + e.getMessage()); }
    }
    
    // 简单模板匹配实现（实际使用建议集成OpenCV）
    private MatchResult matchTemplate(BufferedImage src, BufferedImage tpl, MatchMethod method, double threshold) {
        MatchResult res = new MatchResult();
        res.method = method; res.width = tpl.getWidth(); res.height = tpl.getHeight();
        
        int sw = src.getWidth(), sh = src.getHeight(), tw = tpl.getWidth(), th = tpl.getHeight();
        double bestVal = method == MatchMethod.TM_SQDIFF || method == MatchMethod.TM_SQDIFF_NORMED ? Double.MAX_VALUE : Double.MIN_VALUE;
        int bestX = 0, bestY = 0;
        
        // 简化版匹配：计算归一化相关系数
        for (int y = 0; y <= sh - th; y += 4) {
            for (int x = 0; x <= sw - tw; x += 4) {
                double val = computeNCC(src, tpl, x, y);
                if (method == MatchMethod.TM_SQDIFF_NORMED) val = 1 - val;
                if ((method == MatchMethod.TM_SQDIFF || method == MatchMethod.TM_SQDIFF_NORMED) ? val < bestVal : val > bestVal) {
                    bestVal = val; bestX = x; bestY = y;
                }
            }
        }
        
        res.x = bestX; res.y = bestY;
        res.similarity = method == MatchMethod.TM_SQDIFF_NORMED ? 1 - bestVal : bestVal;
        res.matchValue = bestVal;
        res.found = method.isNormalized() && res.similarity >= threshold;
        if (!method.isNormalized()) res.found = true;
        
        return res;
    }
    
    // 计算归一化相关系数 (NCC)
    private double computeNCC(BufferedImage src, BufferedImage tpl, int ox, int oy) {
        int tw = tpl.getWidth(), th = tpl.getHeight();
        double sumSrc = 0, sumTpl = 0, sumSqSrc = 0, sumSqTpl = 0, sumProd = 0;
        int n = tw * th;
        
        for (int y = 0; y < th; y++) {
            for (int x = 0; x < tw; x++) {
                int rgb1 = src.getRGB(ox + x, oy + y);
                int rgb2 = tpl.getRGB(x, y);
                double g1 = 0.299 * ((rgb1 >> 16) & 0xFF) + 0.587 * ((rgb1 >> 8) & 0xFF) + 0.114 * (rgb1 & 0xFF);
                double g2 = 0.299 * ((rgb2 >> 16) & 0xFF) + 0.587 * ((rgb2 >> 8) & 0xFF) + 0.114 * (rgb2 & 0xFF);
                sumSrc += g1; sumTpl += g2;
                sumSqSrc += g1 * g1; sumSqTpl += g2 * g2;
                sumProd += g1 * g2;
            }
        }
        
        double meanSrc = sumSrc / n, meanTpl = sumTpl / n;
        double stdSrc = Math.sqrt(sumSqSrc / n - meanSrc * meanSrc);
        double stdTpl = Math.sqrt(sumSqTpl / n - meanTpl * meanTpl);
        
        if (stdSrc < 1e-6 || stdTpl < 1e-6) return 0;
        return (sumProd / n - meanSrc * meanTpl) / (stdSrc * stdTpl);
    }
    
    private void clearTestResults() {
        imageDisplayPanel.clearTestResults();
        lblTestResult.setText("测试结果: -");
        lblTestResult.setForeground(new Color(0, 150, 0));
        log("已清除测试结果");
    }
    
    private void takeScreenshot() {
        if (imageDisplayPanel.getImage() == null) { log("当前没有设备画面，请先开始投影"); return; }
        log("进入截图模式，请在右侧显示区框选截图区域（按ESC取消）");
        imageDisplayPanel.startScreenshotMode();
    }
    
    private void onSelectionFinished(int x, int y, int w, int h) {
        BufferedImage src = imageDisplayPanel.getImage();
        if (src == null) { log("截图失败：没有画面"); return; }
        
        try {
            BufferedImage crop = src.getSubimage(x, y, w, h);
            String ts = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
            String filename = "screenshot_" + ts + ".png";
            File dir = new File(picDirectory);
            if (!dir.exists()) dir.mkdirs();
            File out = new File(dir, filename);
            ImageIO.write(crop, "png", out);
            log("截图已保存: " + filename);
            
            // 显示预览
            int pw = screenshotPreview.getWidth() - 10, ph = screenshotPreview.getHeight() - 10;
            double scale = Math.min((double) pw / w, (double) ph / h);
            int sw = (int) (w * scale), sh = (int) (h * scale);
            BufferedImage preview = new BufferedImage(sw, sh, BufferedImage.TYPE_INT_RGB);
            preview.getGraphics().drawImage(crop.getScaledInstance(sw, sh, Image.SCALE_SMOOTH), 0, 0, null);
            screenshotPreview.setText("");
            screenshotPreview.setIcon(new ImageIcon(preview));
        } catch (Exception e) { log("截图失败: " + e.getMessage()); }
    }
    
    public static void main(String[] args) {
        try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); } catch (Exception e) {}
        SwingUtilities.invokeLater(() -> new ImageMatchTestGUI().setVisible(true));
    }
}
