/* 示例视图插件：管理层精简视图（可直接删除或用「📤 导出视图文件」生成自己的） */
window.VIEW_PLUGIN = {
  id: "示例管理层视图",
  name: "示例管理层视图",
  layout: [
    { id: "kpi_overview", x: 0, y: 0, w: 2, h: 2 },
    { id: "kpi_special", x: 2, y: 0, w: 2, h: 2 },
    { id: "kpi_transit", x: 4, y: 0, w: 2, h: 2 },
    { id: "kpi_receive", x: 6, y: 0, w: 2, h: 2 },
    { id: "kpi_rate", x: 8, y: 0, w: 4, h: 2 },
    { id: "chart_type", x: 0, y: 2, w: 4, h: 3 },
    { id: "chart_trend", x: 4, y: 2, w: 8, h: 3 },
    { id: "alert_transit", x: 0, y: 5, w: 6, h: 3 },
    { id: "alert_receive", x: 6, y: 5, w: 6, h: 3 },
    { id: "table_detail", x: 0, y: 8, w: 12, h: 5 }
  ]
};
