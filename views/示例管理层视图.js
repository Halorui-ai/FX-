/* 示例视图插件：管理层精简视图（可直接删除或用「📤 导出视图文件」生成自己的） */
window.VIEW_PLUGIN = {
  id: "示例管理层视图",
  name: "示例管理层视图",
  layout: [
    { id: "kpi_overview", x: 0, y: 0, w: 4, h: 4 },
    { id: "kpi_special", x: 4, y: 0, w: 4, h: 4 },
    { id: "kpi_transit", x: 8, y: 0, w: 4, h: 4 },
    { id: "kpi_receive", x: 12, y: 0, w: 4, h: 4 },
    { id: "kpi_rate", x: 16, y: 0, w: 8, h: 4 },
    { id: "chart_type", x: 0, y: 4, w: 8, h: 6 },
    { id: "chart_trend", x: 8, y: 4, w: 16, h: 6 },
    { id: "alert_transit", x: 0, y: 10, w: 12, h: 6 },
    { id: "alert_receive", x: 12, y: 10, w: 12, h: 6 },
    { id: "table_detail", x: 0, y: 16, w: 24, h: 10 }
  ]
};
