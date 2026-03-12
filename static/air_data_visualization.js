// 模拟用户数据库
const users = [];
let currentUser = null;
let loadingOverlay = null;

// 显示加载动画
function showLoading() {
  if (!loadingOverlay) {
    loadingOverlay = document.createElement("div");
    loadingOverlay.id = "loading-overlay";
    loadingOverlay.style.position = "fixed";
    loadingOverlay.style.top = "0";
    loadingOverlay.style.left = "0";
    loadingOverlay.style.width = "100%";
    loadingOverlay.style.height = "100%";
    loadingOverlay.style.backgroundColor = "rgba(0, 0, 0, 0.5)";
    loadingOverlay.style.display = "flex";
    loadingOverlay.style.justifyContent = "center";
    loadingOverlay.style.alignItems = "center";
    const spinner = document.createElement("div");
    spinner.classList.add("spinner");
    loadingOverlay.appendChild(spinner);
    document.body.appendChild(loadingOverlay);
  }
  loadingOverlay.style.display = "flex";
}

// 隐藏加载动画
function hideLoading() {
  if (loadingOverlay) {
    loadingOverlay.style.display = "none";
  }
}

async function handleLogin() {
  showLoading();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const userType = document.getElementById("userType").value;

  // 输入验证
  if (!username) {
    hideLoading();
    alert("请输入账号");
    return;
  }
  if (!password) {
    hideLoading();
    alert("请输入密码");
    return;
  }
  if (username.length < 3 || username.length > 6) {
    hideLoading();
    alert("账号长度需在3到6位之间");
    return;
  }
  if (password.length < 3 || password.length > 6) {
    hideLoading();
    alert("密码长度需在3到6位之间");
    return;
  }
  try {
    // 统一通过后端验证（包括管理员账号）
    const response = await fetch("/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      credentials: "include",
      body: `username=${username}&password=${password}&user_type=${userType}`,
    });
    const data = await response.json();
    if (data.message === "登录成功") {
      currentUser = { username, userType };
      showDashboard();
      showSystemManagement();
    } else {
      alert(data.message);
    }
  } catch (error) {
    alert("登录失败，请稍后重试");
  }
  hideLoading();
}

async function handleRegister() {
  showLoading();
  const registerUsername = document.getElementById("registerUsername").value;
  const registerPassword = document.getElementById("registerPassword").value;
  const registerUserType = "user"; // 强制设置普通用户类型

  // 输入验证
  if (!registerUsername) {
    hideLoading();
    alert("请输入账号");
    return;
  }
  if (!registerPassword) {
    hideLoading();
    alert("请输入密码");
    return;
  }
  if (registerUsername.length < 3 || registerUsername.length > 6) {
    hideLoading();
    alert("账号长度需在3到6位之间");
    return;
  }
  if (registerPassword.length < 3 || registerPassword.length > 6) {
    hideLoading();
    alert("密码长度需在3到6位之间");
    return;
  }

  try {
    const response = await fetch("/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      credentials: "include",
      body: `username=${registerUsername}&password=${registerPassword}&user_type=${registerUserType}`,
    });
    const data = await response.json();
    if (data.message === "账户创建成功") {
      showLoginPage();
      alert("注册成功");
    } else {
      alert(data.message);
    }
  } catch (error) {
    alert("注册失败，请稍后重试");
  }
  hideLoading();
}

function showLoginPage() {
  document.getElementById("registerPage").style.display = "none";
  document.getElementById("loginPage").style.display = "flex";
  document.getElementById("dashboardPage").style.display = "none";
}

function showRegisterPage() {
  document.getElementById("registerPage").style.display = "flex";
  document.getElementById("loginPage").style.display = "none";
  document.getElementById("dashboardPage").style.display = "none";
}

function showDashboard() {
  document.getElementById("loginPage").style.display = "none";
  document.getElementById("dashboardPage").style.display = "flex";
  const loginTime = new Date().toLocaleString();
  document.getElementById("loginTime").textContent = `登录时间：${loginTime}`;
  document.querySelector(".user-name").textContent = currentUser.username;
  showHomePage();
}

function showHomePage() {
  document.getElementById("homePage").style.display = "block";
  document.getElementById("dataAnalysisPage").style.display = "none";
  document.getElementById("profilePage").style.display = "none";
  document.getElementById("changePasswordPage").style.display = "none";
  document.getElementById("userManagementPage").style.display = "none";
  document.getElementById("weatherPage").style.display = "none";
}

function showDataAnalysisPage() {
  document.getElementById("homePage").style.display = "none";
  document.getElementById("dataAnalysisPage").style.display = "block";
  document.getElementById("profilePage").style.display = "none";
  document.getElementById("changePasswordPage").style.display = "none";
  document.getElementById("userManagementPage").style.display = "none";
  document.getElementById("weatherPage").style.display = "none";
}

function showSystemManagement() {
  const systemManagementDrawer = document.getElementById(
    "systemManagementDrawer"
  );
  if (currentUser && currentUser.userType === "admin") {
    systemManagementDrawer.style.display = "block"; // 管理员显示
  } else {
    systemManagementDrawer.style.display = "none"; // 普通用户隐藏
  }
}

function showProfilePage() {
  document.getElementById("homePage").style.display = "none";
  document.getElementById("dataAnalysisPage").style.display = "none";
  document.getElementById("profilePage").style.display = "block";
  document.getElementById("changePasswordPage").style.display = "none";
  document.getElementById("userManagementPage").style.display = "none";
  document.getElementById("weatherPage").style.display = "none";
  document.getElementById("profileUsername").value = currentUser.username;
  document.getElementById("profileUserType").value = currentUser.userType;
}

function showChangePasswordPage() {
  document.getElementById("homePage").style.display = "none";
  document.getElementById("dataAnalysisPage").style.display = "none";
  document.getElementById("profilePage").style.display = "none";
  document.getElementById("changePasswordPage").style.display = "block";
  document.getElementById("userManagementPage").style.display = "none";
  document.getElementById("weatherPage").style.display = "none";
}

async function showUserManagement() {
  document.getElementById("homePage").style.display = "none";
  document.getElementById("dataAnalysisPage").style.display = "none";
  document.getElementById("profilePage").style.display = "none";
  document.getElementById("changePasswordPage").style.display = "none";
  document.getElementById("userManagementPage").style.display = "block";
  document.getElementById("weatherPage").style.display = "none";

  // 获取用户列表
  try {
    const response = await fetch("/api/users", {
      credentials: "include",
    });
    const users = await response.json();

    // 渲染用户列表到userList div
    const userListDiv = document.getElementById("userList");
    userListDiv.innerHTML = "";

    users.forEach((user) => {
      const userItem = document.createElement("div");
      userItem.className = "user-item";
      userItem.innerHTML = `
                <span>${user.username}</span>
                <select class="user-type-select" data-user-id="${user.id}">
                    <option value="user" ${
                      user.user_type === "user" ? "selected" : ""
                    }>普通用户</option>
                    <option value="admin" ${
                      user.user_type === "admin" ? "selected" : ""
                    }>管理员</option>
                </select>
                <button class="delete-btn" data-user-id="${
                  user.id
                }">删除</button>
            `;

      userListDiv.appendChild(userItem);
    });

    // 绑定权限修改事件
    document.querySelectorAll(".user-type-select").forEach((select) => {
      select.addEventListener("change", async function () {
        const userId = this.dataset.userId;
        const newType = this.value;
        try {
          await fetch(`/api/user/${userId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ userType: newType }),
          });
          alert("权限更新成功");
          showUserManagement(); // 刷新列表
        } catch (error) {
          alert("权限修改失败");
        }
      });
    });

    // 绑定删除用户事件
    document.querySelectorAll(".delete-btn").forEach((button) => {
      button.addEventListener("click", async function () {
        const userId = this.dataset.userId;
        if (confirm("确认删除该用户？")) {
          try {
            await fetch(`/api/user/${userId}`, {
              method: "DELETE",
              credentials: "include",
            });
            alert("用户删除成功");
            showUserManagement(); // 刷新列表
          } catch (error) {
            alert("删除失败");
          }
        }
      });
    });
  } catch (error) {
    alert("获取用户列表失败");
  }
}

async function saveProfile() {
  const newUsername = document.getElementById("profileUsername").value;
  const avatarFile = document.getElementById("profileAvatar").files[0];

  const formData = new FormData(); // 使用FormData处理文件和文本
  formData.append("username", newUsername);
  if (avatarFile) formData.append("avatar", avatarFile); // 添加头像文件

  try {
    const res = await fetch("/api/update_profile", {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    const data = await res.json();
    if (data.success) {
      alert("保存成功");
      // 更新全局用户对象和页面显示
      currentUser.username = newUsername;
      document.querySelector(".user-name").textContent = newUsername;
      const headerAvatar = document.querySelector(".user-avatar");
      if (headerAvatar) {
        headerAvatar.src = avatarFile
          ? URL.createObjectURL(avatarFile)
          : "/static/default-avatar.png"; // 默认头像路径需根据实际路径调整
      }
      // 更新头像预览
      if (avatarFile) {
        document.getElementById("previewAvatar").src =
          URL.createObjectURL(avatarFile);
      }
    } else {
      alert(data.error);
    }
  } catch (error) {
    alert("保存失败");
  }
}

function handleLogout() {
  currentUser = null;
  document.getElementById("loginPage").style.display = "flex";
  document.getElementById("dashboardPage").style.display = "none";
  document.getElementById("registerPage").style.display = "none";
  const logoutMessage = document.getElementById("logoutMessage");
  logoutMessage.textContent = "退出成功";
  setTimeout(() => {
    logoutMessage.textContent = "";
  }, 3000);
}

async function addUser() {
  showLoading();
  const newUserUsername = document.getElementById("newUserUsername").value;
  const newUserPassword = document.getElementById("newUserPassword").value;
  const newUserType = document.getElementById("newUserType").value;

  // 输入验证
  if (!newUserUsername) {
    hideLoading();
    alert("请输入新用户账号");
    return;
  }
  if (!newUserPassword) {
    hideLoading();
    alert("请输入新用户密码");
    return;
  }

  try {
    const response = await fetch("/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      credentials: "include",
      body: `username=${newUserUsername}&password=${newUserPassword}&user_type=${newUserType}`,
    });
    const data = await response.json();
    if (data.message === "账户创建成功") {
      alert("用户添加成功");
      showUserManagement(); // 刷新列表
    } else {
      alert(data.message);
    }
  } catch (error) {
    alert("添加用户失败");
  }
  hideLoading();
}

// 修改日期参数处理
async function fetchChartDataWithDate() {
  const startDateInput = document.getElementById("startDate").value;
  const endDateInput = document.getElementById("endDate").value;

  if (!startDateInput || !endDateInput) {
    alert("请选择开始时间和结束时间");
    return;
  }

  // 补充日期为1日
  const startDate = `${startDateInput}-01`;
  const endDate = `${endDateInput}-01`;

  const charts = [
    "aqiTrend",
    "pollutantComparison",
    "qualityDistribution",
    "correlationHeatmap",
  ];
  charts.forEach((id) => {
    const chart = document.getElementById(id);
    if (chart.style.display === "block") {
      fetchChartData(id, startDate, endDate);
    }
  });
}

async function fetchChartData(chartType, startDate, endDate) {
  showLoading();
  try {
    const backendChartType = chartType.replace(/([A-Z])/g, "_$1").toLowerCase();
    const response = await fetch(
      `/visualize/${backendChartType}?start_date=${startDate}&end_date=${endDate}`,
      {
        credentials: "include",
      }
    );
    const data = await response.json();

    document.getElementById(
      `${chartType}Img`
    ).src = `data:image/png;base64,${data.chart_data}`;
    const analysisSection = document.getElementById(`${chartType}Analysis`);
    analysisSection.innerHTML = `
            <h4>数据分析</h4>
            <div class="analysis-content">
                ${data.analysis_text
                  .split("\n")
                  .map((line) => `<p>${line}</p>`)
                  .join("")}
            </div>
        `;
  } catch (error) {
    alert("图表数据请求失败，请稍后重试");
  }
  hideLoading();
}

function toggleSubmenu(item) {
  document.querySelectorAll(".sidebar-item.has-submenu").forEach((el) => {
    el.classList.remove("open");
  });
  item.classList.toggle("open");
}

function toggleDrawer() {
  const drawer = document.getElementById("dataAnalysisDrawer");
  const arrow = document.getElementById("drawerArrow");
  drawer.classList.toggle("open");
  arrow.classList.toggle("fa-chevron-down");
  arrow.classList.toggle("fa-chevron-up");
}

function toggleSystemManagementDrawer() {
  const drawer = document.getElementById("systemManagementDrawer");
  const arrow = document.getElementById("systemManagementArrow");
  drawer.classList.toggle("open");
  arrow.classList.toggle("fa-chevron-down");
  arrow.classList.toggle("fa-chevron-up");
}

document.addEventListener("DOMContentLoaded", () => {
  // 初始化系统管理抽屉状态
  showSystemManagement();

  // 清空图表
  document.getElementById("aqiTrendImg").src = "";
  document.getElementById("pollutantComparisonImg").src = "";
  document.getElementById("qualityDistributionImg").src = "";
  document.getElementById("correlationHeatmapImg").src = "";
});

async function showChart(chartId) {
  showDataAnalysisPage();
  const charts = [
    "aqiTrend",
    "pollutantComparison",
    "qualityDistribution",
    "correlationHeatmap",
  ];
  charts.forEach((id) => {
    const chart = document.getElementById(id);
    if (id === chartId) {
      chart.style.display = "block";
      // 清空其他图表的 src 属性
      charts.forEach((otherId) => {
        if (otherId !== id) {
          document.getElementById(`${otherId}Img`).src = "";
        }
      });
      // 调用 fetchChartDataWithDate 进行日期验证
      fetchChartDataWithDate();
    } else {
      chart.style.display = "none";
    }
  });
}

async function handleChangePassword() {
  showLoading();
  const currentPassword = document.getElementById("currentPassword").value;
  const newPassword = document.getElementById("newPassword").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  // 基础验证
  if (!currentPassword || !newPassword || !confirmPassword) {
    hideLoading();
    alert("所有字段均为必填");
    return;
  }
  if (newPassword !== confirmPassword) {
    hideLoading();
    alert("两次输入的密码不一致");
    return;
  }

  try {
    const response = await fetch("/change_password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        currentPassword,
        newPassword,
      }),
    });
    const data = await response.json();
    if (data.success) {
      alert("密码修改成功");
      handleLogout();
    } else {
      alert(data.message);
    }
  } catch (error) {
    alert("密码修改失败，请稍后再试");
  } finally {
    hideLoading();
  }
}

document
  .getElementById("profileAvatar")
  .addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        document.getElementById("previewAvatar").src = event.target.result;
      };
      reader.readAsDataURL(file);
    }
  });

// 天气预测相关函数
function showWeatherPage() {
  document.getElementById("homePage").style.display = "none";
  document.getElementById("dataAnalysisPage").style.display = "none";
  document.getElementById("profilePage").style.display = "none";
  document.getElementById("changePasswordPage").style.display = "none";
  document.getElementById("userManagementPage").style.display = "none";
  document.getElementById("weatherPage").style.display = "block";

  // 确保DOM元素渲染完成后再加载天气数据
  setTimeout(function() {
    loadCurrentWeather();
    loadWeatherForecast();
    // 默认显示温度趋势图表
    showWeatherChart('temperature_trend');
  }, 100);
}

// 获取当前天气数据
async function loadCurrentWeather() {
  try {
    showLoading();
    const response = await fetch("/api/weather/current", {
      credentials: "include",
    });
    const data = await response.json();

    if (data.success) {
      displayCurrentWeather(data.data);
    } else {
      console.error("获取当前天气失败:", data.message);
      alert("获取当前天气失败");
    }
  } catch (error) {
    console.error("获取当前天气出错:", error);
    alert("获取当前天气出错");
  } finally {
    hideLoading();
  }
}

// 显示当前天气
function displayCurrentWeather(weather) {
  const currentWeatherContent = document.getElementById("currentWeatherContent");
  
  if (!currentWeatherContent) {
    console.error("找不到currentWeatherContent元素");
    return;
  }
  
  currentWeatherContent.innerHTML = `
    <div class="weather-info">
      <div class="weather-main">
        <div class="temperature">${Math.round(weather.temperature)}°C</div>
        <div class="description">
          <i class="fa-solid fa-${getWeatherIcon(weather.description)}"></i> 
          ${weather.description}
        </div>
      </div>
      <div class="weather-details">
        <div class="detail-item">
          <span class="label"><i class="fa-solid fa-wind"></i> 风速</span>
          <span class="value">${weather.wind_speed} m/s</span>
        </div>
        <div class="detail-item">
          <span class="label"><i class="fa-solid fa-gauge"></i> 气压</span>
          <span class="value">${weather.pressure} hPa</span>
        </div>
        <div class="detail-item">
          <span class="label"><i class="fa-solid fa-temperature-high"></i> 体感温度</span>
          <span class="value">${Math.round(weather.feels_like)}°C</span>
        </div>
      </div>
    </div>
  `;
}

// 根据天气描述返回Font Awesome图标类名
function getWeatherIcon(description) {
  const iconMap = {
    '晴': 'sun',
    '多云': 'cloud-sun',
    '阴': 'cloud',
    '小雨': 'cloud-rain',
    '中雨': 'cloud-showers-heavy',
    '大雨': 'cloud-showers-heavy',
    '雷阵雨': 'bolt',
    '雪': 'snowflake',
    '雾': 'smog'
  };
  
  for (const key in iconMap) {
    if (description.includes(key)) {
      return iconMap[key];
    }
  }
  
  return 'sun'; // 默认图标
}

// 获取天气预报数据
async function loadWeatherForecast() {
  try {
    const response = await fetch("/api/weather/forecast", {
      credentials: "include",
    });
    const data = await response.json();

    if (data.success) {
      displayWeatherForecast(data.data);
    } else {
      console.error("获取天气预报失败:", data.message);
    }
  } catch (error) {
    console.error("获取天气预报出错:", error);
  }
}

// 显示15天天气预报
function displayWeatherForecast(forecast) {
  const forecastContainer = document.getElementById("weatherForecastContent");
  
  if (!forecastContainer) {
    console.error("找不到weatherForecastContent元素");
    return;
  }
  
  forecastContainer.innerHTML = "";

  // 创建预报网格容器
  const forecastGrid = document.createElement("div");
  forecastGrid.className = "forecast-grid";

  forecast.forEach((day, index) => {
    const dayElement = document.createElement("div");
    dayElement.className = "forecast-day";
    
    // 特殊处理今天、明天、后天
    let displayDate = day.date;
    if (day.day === '今天' || day.day === '明天' || day.day === '后天') {
      displayDate = day.day;
    } else {
      displayDate = formatDate(day.date);
    }
    
    dayElement.innerHTML = `
      <div class="forecast-header">
        <div class="forecast-date">
          <i class="fa-solid fa-calendar"></i> ${displayDate}
        </div>
        <div class="forecast-day-name">${day.day}</div>
      </div>
      <div class="forecast-weather">
        <div class="forecast-icon-container">
          ${day.icon_url ? 
            `<img src="${day.icon_url}" alt="${day.description}" class="weather-icon-img">` :
            `<i class="fa-solid fa-${getWeatherIcon(day.description)} forecast-icon-fallback"></i>`
          }
        </div>
        <div class="forecast-desc">
          ${day.description}
        </div>
      </div>
      <div class="forecast-temps">
        <div class="temp-high">
          <i class="fa-solid fa-temperature-high"></i> 
          ${Math.round(day.max_temp)}°
        </div>
        <div class="temp-low">
          <i class="fa-solid fa-temperature-low"></i> 
          ${Math.round(day.min_temp)}°
        </div>
      </div>
      <div class="forecast-details">
        <div class="forecast-rain-prob">
          <i class="fa-solid fa-cloud-rain"></i> 
          ${Math.round(day.max_rain_prob)}%
        </div>
      </div>
    `;
    
    // 为今天、明天、后天添加特殊样式
    if (index === 0) {
      dayElement.classList.add('forecast-today');
    } else if (index === 1) {
      dayElement.classList.add('forecast-tomorrow');
    } else if (index === 2) {
      dayElement.classList.add('forecast-day-after');
    }
    
    forecastGrid.appendChild(dayElement);
  });
  
  forecastContainer.appendChild(forecastGrid);
}

// 格式化日期
function formatDate(dateString) {
  const date = new Date(dateString);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  if (date.toDateString() === today.toDateString()) {
    return "今天";
  } else if (date.toDateString() === tomorrow.toDateString()) {
    return "明天";
  } else {
    return `${date.getMonth() + 1}/${date.getDate()}`;
  }
}

// 显示天气图表的统一入口函数
function showWeatherChart(chartType) {
  // 首先检查DOM元素是否存在
  const chartTabs = document.querySelectorAll('.chart-tab');
  if (!chartTabs || chartTabs.length === 0) {
    console.error('找不到图表标签页元素');
    return;
  }
  
  // 设置活跃标签页
  chartTabs.forEach(tab => {
    tab.classList.remove('active');
  });
  
  // 根据图表类型加载对应的数据
  switch(chartType) {
    case 'temperature_trend':
      // 设置温度趋势按钮为活跃状态
      chartTabs[0].classList.add('active');
      loadWeatherChart('temperature');
      break;
    case 'rain_probability':
      // 设置降雨概率按钮为活跃状态
      chartTabs[1].classList.add('active');
      loadWeatherChart('rain');
      break;
    default:
      console.error('未知的图表类型:', chartType);
      // 默认显示温度趋势
      chartTabs[0].classList.add('active');
      loadWeatherChart('temperature');
  }
}

// 天气图表相关变量
let weatherChart = null;

// 显示温度趋势图表
async function showTemperatureChart() {
  setActiveChartButton("tempBtn");
  await loadWeatherChart("temperature");
}

// 显示降雨概率图表
async function showRainChart() {
  setActiveChartButton("rainBtn");
  await loadWeatherChart("rain");
}

// 设置活跃的图表按钮
function setActiveChartButton(activeId) {
  document.querySelectorAll(".chart-btn").forEach((btn) => {
    btn.classList.remove("active");
  });
  document.getElementById(activeId).classList.add("active");
}

// 加载天气图表数据
async function loadWeatherChart(chartType) {
  try {
    showLoading();
    const response = await fetch(`/api/weather/charts/${chartType}`, {
      credentials: "include",
    });
    const data = await response.json();

    if (data.success) {
      renderWeatherChart(data.data, chartType);
    } else {
      console.error("获取图表数据失败:", data.message);
      alert("获取图表数据失败");
    }
  } catch (error) {
    console.error("获取图表数据出错:", error);
    alert("获取图表数据出错");
  } finally {
    hideLoading();
  }
}

// 渲染天气图表
function renderWeatherChart(chartData, chartType) {
  const canvas = document.getElementById("weatherChart");
  
  if (!canvas) {
    console.error("找不到weatherChart元素");
    return;
  }
  
  const ctx = canvas.getContext("2d");

  // 销毁之前的图表
  if (weatherChart) {
    weatherChart.destroy();
  }

  // 根据图表类型设置配置
  let config = {
    type: "line",
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: getChartLabel(chartType),
          data: chartData.values,
          borderColor: getChartColor(chartType),
          backgroundColor: getChartColor(chartType) + "20",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: getChartTitle(chartType),
        },
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: chartType === "rain",
          title: {
            display: true,
            text: getYAxisLabel(chartType),
          },
        },
        x: {
          title: {
            display: true,
            text: "时间",
          },
        },
      },
    },
  };

  // 创建新图表
  weatherChart = new Chart(ctx, config);
}

// 获取图表标签
function getChartLabel(chartType) {
  const labels = {
    temperature: "温度",
    rain: "降雨概率",
  };
  return labels[chartType] || "数据";
}

// 获取图表颜色
function getChartColor(chartType) {
  const colors = {
    temperature: "#ff6b6b",
    rain: "#45b7d1",
  };
  return colors[chartType] || "#666";
}

// 获取图表标题
function getChartTitle(chartType) {
  const titles = {
    temperature: "未来24小时温度趋势",
    rain: "未来24小时降雨概率",
  };
  return titles[chartType] || "天气趋势";
}

// 获取Y轴标签
function getYAxisLabel(chartType) {
  const labels = {
    temperature: "温度 (°C)",
    rain: "降雨概率 (%)",
  };
  return labels[chartType] || "数值";
}
