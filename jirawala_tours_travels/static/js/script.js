// =====================================================
// TAXI BOOKING SYSTEM - FRONTEND JAVASCRIPT
// =====================================================

// =====================================================
// 📋 TABLE OF CONTENTS / INDEX
// =====================================================
/*
┌─────────────────────────────────────────────────────────────────┐
│                    🚖TAXI BOOKING SYSTEM                        │
│                     JavaScript Index                            │
└─────────────────────────────────────────────────────────────────┘

📍 SECTION 1: GLOBAL VARIABLES & CONFIGURATION (Line ~50)
   ├── Booking state management variables
   ├── API configuration constants
   ├── Dynamic car types storage
   └── System-wide settings

📍 SECTION 2: UTILITY FUNCTIONS (Line ~65)
   ├── easeOutQuart() - Animation easing function
   ├── formatDateTimeLocal() - Date formatting helper
   ├── getCSRFToken() - Security token retrieval
   └── getURLParameters() - URL parameter parsing

📍 SECTION 2.1: TOOLTIP INITIALIZATION
   ├── initCarTypeTooltips() - Initialize tooltips for car types

📍 SECTION 3: DYNAMIC CAR TYPES MANAGEMENT (Line ~90)
   ├── loadDynamicCarTypes() - Fetch car types from API
   ├── getCarTypeRate() - Get current rate for car type
   ├── updateCarTypePricing() - Update UI with dynamic rates
   ├── refreshCarTypesForModal() - Refresh modal car types
   └── loadFallbackCarTypes() - Fallback to hardcoded rates

📍 SECTION 4: ANIMATION & VISUAL EFFECTS (Line ~180)
   ├── animateCounters() - Stats counter animations
   ├── initializeScrollAnimations() - Scroll-based animations
   └── initializeEnhancedCarAnimations() - Car card animations

📍 SECTION 5: NAVIGATION & SCROLLING (Line ~280)
   ├── initializeNavigation() - Smooth scrolling setup
   └── initializeBreadcrumbs() - Breadcrumb navigation

📍 SECTION 6: FORM HANDLING & VALIDATION (Line ~340)
   ├── initializeTripTypeToggle() - Trip type selection
   ├── initializeQuickSelect() - Quick date selection
   ├── validateBookingForm() - Form validation logic
   └── initializeBookingFormPrefill() - Pre-fill form from URL params

📍 SECTION 7: ENHANCED DISTANCE CALCULATION & ROUTE INFO (Line ~480)
   ├── calculateDistanceMatrix() - Primary API distance calculation
   ├── calculateDistancePlaceholder() - Fallback distance calculation
   ├── updateRouteInformation() - ENHANCED: Dynamic route info display
   ├── calculateEstimatedDuration() - NEW: Travel time estimation
   └── updateCarPrices() - UPDATED: Price updates with dynamic rates

📍 SECTION 8: BOOKING SYSTEM & MODAL MANAGEMENT (Line ~620)
   ├── initializeDistanceCalculation() - Distance calculation setup
   ├── handleBookingConfirmation() - Booking confirmation logic
   └── handleModalClose() - Modal cleanup

📍 SECTION 9: BACKEND API COMMUNICATION (Line ~820)
   ├── submitBookingRequest() - Backend booking submission
   └── checkBookingStatus() - Booking status verification

📍 SECTION 10: UI COMPONENTS & INTERACTIONS (Line ~920)
   ├── initializeCarBookingButtons() - Car selection buttons
   ├── initializeFilteringSystem() - BRAND NEW FILTERING SYSTEM
   ├── initializeEnhancedCarBooking() - Enhanced car booking
   ├── initializeRouteBookingButtons() - Route booking with prefill
   └── initializeOurCarsBookingButtons() - NEW: Our Cars page booking

📍 SECTION 11: GALLERY FUNCTIONS
   ├── initializeGallery() - Gallery initialization
   ├── filterGalleryItems() - Gallery filtering logic
   └── openGalleryItem() - Open selected gallery item

📍 SECTION 12: SUCCESS NOTIFICATIONS & FEEDBACK (Line ~1050)
   └── showEnhancedBookingSuccess() - Success modal display

📍 SECTION 13: CAROUSEL & INTERACTIVE COMPONENTS (Line ~1150)
   └── initializeServicesCarousel() - FIXED Swiper carousel setup

📍 SECTION 14: FORM UTILITIES & HELPERS (Line ~1250)
   ├── initializeBookingForm() - Form initialization
   └── resetBookingForm() - Form reset functionality

📍 SECTION 15: RESPONSIVE & ACCESSIBILITY UTILITIES (Line ~1280)
   ├── handleEnhancedResponsiveChanges() - Mobile responsiveness
   └── addKeyboardSupport() - Keyboard navigation

📍 SECTION 16: INITIALIZATION & EVENT LISTENERS (Line ~1320)
   └── Main DOM Content Loaded Event - System startup

📍 SECTION 17: CSS INJECTION FOR ANIMATIONS (Line ~1380)
   └── Dynamic CSS injection for animations

📍 SECTION 18: EXPORT UTILITIES (Line ~1450)
   └── Public API exports for external use

*/

// =====================================================
// 1. GLOBAL VARIABLES & CONFIGURATION
// =====================================================

// Booking state management
let isBookingInProgress = false
let currentModal = null
let selectedCar = null
let calculatedDistance = 0

// Dynamic car types storage
let dynamicCarTypes = {}
let isCarTypesLoaded = false

// Distance-Matrix API Configuration
// const DISTANCE_MATRIX_API_KEY = "9rmBnCVMJAN8qPoxHROmBoNpXm4qQHPL5b6ttlnQbEzziHh28SSdBJ6zmNEZP1DI"
// const API_TIMEOUT = 10000 // 10 seconds

// Google Maps API Configuration
// --- Distance/ETA helpers (safe) ---
let routeInfoPlaceholderTimer = null;

function toMessage(err) {
  try {
    if (!err) return "Unknown error";
    if (typeof err === "string") return err;
    if (err && typeof err === "object" && "message" in err) return String(err.message || "Unknown error");
    return String(err);
  } catch (_) {
    return "Unknown error";
  }
}


// =====================================================
// 2. UTILITY FUNCTIONS
// =====================================================

// Easing function for smooth animations
function easeOutQuart(t) {
  return 1 - --t * t * t * t
}

// Helper function to format date for datetime-local input
function formatDateTimeLocal(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

// Helper to get CSRF token from cookie
function getCSRFToken() {
  const name = "csrftoken"
  const cookies = document.cookie.split(";")
  for (let i = 0; i < cookies.length; i++) {
    const c = cookies[i].trim()
    if (c.startsWith(name + "=")) {
      return decodeURIComponent(c.substring(name.length + 1))
    }
  }
  return ""
}

// 🆕 NEW: Helper function to get URL parameters
function getURLParameters() {
  const params = new URLSearchParams(window.location.search)
  const hash = window.location.hash

  // Check if parameters are in the hash (for anchor links with params)
  if (hash && hash.includes("?")) {
    const hashParams = new URLSearchParams(hash.split("?")[1])
    const result = {}

    // Get parameters from hash
    for (const [key, value] of hashParams.entries()) {
      result[key] = decodeURIComponent(value)
    }

    // Also check regular URL parameters
    for (const [key, value] of params.entries()) {
      result[key] = decodeURIComponent(value)
    }

    return result
  }

  // Regular URL parameters
  const result = {}
  for (const [key, value] of params.entries()) {
    result[key] = decodeURIComponent(value)
  }

  return result
}

// =====================================================
// 📍 SECTION 2.1: TOOLTIP INITIALIZATION
// =====================================================

function initCarTypeTooltips() {
  fetch("/api/available-cars-by-type/")
    .then(res => res.json())
    .then(data => {
      if (data.success) {

        // 🧹 Remove any old tooltip DOM elements
        document.querySelectorAll('.tooltip').forEach(tip => tip.remove());

        document.querySelectorAll('.car-option').forEach(option => {
          const type = option.querySelector('h6')?.textContent.trim();
          const cars = data.data[type] || [];

          // Simple tooltip text
          let tooltipText = "Available Car's :<br>";
          tooltipText += cars.length > 0 ? cars.join('<br>') : 'No cars available';

          option.removeAttribute('title');
          option.setAttribute('data-bs-original-title', tooltipText);
          option.setAttribute('data-bs-html', 'true');
        });

        // Initialize Bootstrap tooltips (HTML enabled)
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('.car-option'));
        tooltipTriggerList.map(el => new bootstrap.Tooltip(el, { html: true }));
      }
    })
    .catch(err => console.error('Error fetching available cars:', err));
}


// =====================================================
// 3. 🆕 DYNAMIC CAR TYPES MANAGEMENT - UPDATED WITH MIN/MAX RATES
// =====================================================

// FUNCTION TO FETCH DYNAMIC CAR TYPES FROM API WITH MIN/MAX RATES
async function loadDynamicCarTypes() {
  try {
    console.log("🚗 Loading dynamic car types from API...")

    const timestamp = new Date().getTime()
    const cacheBuster = Math.random().toString(36).substring(7)
    const url = `/api/car-types/?t=${timestamp}&cb=${cacheBuster}`

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
      },
    })

    const data = await response.json()

    if (data.success && data.car_types) {
      // Store car types in global variable
      dynamicCarTypes = {}
      data.car_types.forEach((carType) => {
        dynamicCarTypes[carType.name] = {
          id: carType.id,
          name: carType.name,
          display_name: carType.display_name,
          rate_per_km: carType.rate_per_km,
          minimum_rate_per_km: carType.minimum_rate_per_km,
          maximum_rate_per_km: carType.maximum_rate_per_km,
          minimum_distance_cap: carType.minimum_distance_cap,
          is_active: carType.is_active,
        }
      })

      isCarTypesLoaded = true
      console.log("✅ Dynamic car types loaded:", dynamicCarTypes)
      console.log("📊 API Response timestamp:", data.timestamp)

      return dynamicCarTypes
    } else {
      console.error("❌ Failed to load car types:", data.error || "Unknown error")
      loadFallbackCarTypes()
      return null
    }
  } catch (error) {
    console.error("❌ Error fetching car types:", error)
    loadFallbackCarTypes()
    return null
  }
}

// FALLBACK FUNCTION WITH MIN/MAX RATES
function loadFallbackCarTypes() {
  console.log("⚠️ Using fallback car types with hardcoded rates")
  dynamicCarTypes = {
    hatchback: {
      id: 1,
      name: "hatchback",
      display_name: "Hatchback",
      rate_per_km: 12,
      minimum_rate_per_km: 10,
      maximum_rate_per_km: 14,
      minimum_distance_cap: 0,
      is_active: true,
    },
    sedan: {
      id: 2,
      name: "sedan",
      display_name: "Sedan",
      rate_per_km: 15,
      minimum_rate_per_km: 13,
      maximum_rate_per_km: 17,
      minimum_distance_cap: 0,
      is_active: true,
    },
    suv: {
      id: 3,
      name: "suv",
      display_name: "SUV",
      rate_per_km: 18,
      minimum_rate_per_km: 16,
      maximum_rate_per_km: 20,
      minimum_distance_cap: 0,
      is_active: true,
    },
  }
  isCarTypesLoaded = true
}

// Function to get min/max rates for round-trip pricing
function getCarTypeRates(carTypeName) {
  const normalizedName = carTypeName.toLowerCase()
  if (dynamicCarTypes[normalizedName]) {
    return {
      oneWayRate: dynamicCarTypes[normalizedName].rate_per_km,
      minRate: dynamicCarTypes[normalizedName].minimum_rate_per_km,
      maxRate: dynamicCarTypes[normalizedName].maximum_rate_per_km,
    }
  }

  // Fallback rates if not found
  const fallbackRates = {
    hatchback: { oneWayRate: 12, minRate: 10, maxRate: 14 },
    sedan: { oneWayRate: 15, minRate: 13, maxRate: 17 },
    suv: { oneWayRate: 18, minRate: 16, maxRate: 20 },
  }

  return fallbackRates[normalizedName] || { oneWayRate: 15, minRate: 13, maxRate: 17 }
}

// Function to refresh car types in modal
async function refreshCarTypesForModal() {
  console.log("🔄 Refreshing car types for modal...")

  // Show loading state
  const pricingOptions = document.querySelector(".pricing-options")
  if (pricingOptions) {
    pricingOptions.innerHTML = `
      <h6 class="mb-3">Loading car types...</h6>
      <div class="text-center">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `
  }

  // Load fresh car types
  await loadDynamicCarTypes()

  // Rebuild the car options UI
  buildDynamicCarOptions()

  // Update prices with current distance
  if (calculatedDistance > 0) {
    updateCarPrices(calculatedDistance)
  }
}

// Function to build dynamic car options in modal
function buildDynamicCarOptions() {
  const pricingOptions = document.querySelector(".pricing-options")
  if (!pricingOptions) return

  const tripType = document.getElementById("tripType")?.value || "one-way"

  // Get active car types
  const activeCarTypes = Object.values(dynamicCarTypes).filter((carType) => carType.is_active)

  if (activeCarTypes.length === 0) {
    pricingOptions.innerHTML = `
      <h6 class="mb-3">No car types available</h6>
      <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle me-2"></i>
        No active car types found. Please contact support.
      </div>
    `
    return
  }

  // Build car options HTML
  let carOptionsHTML = `<h6 class="mb-3">Select Your Car Type & View Pricing:</h6><div class="row g-3">`

  activeCarTypes.forEach((carType, index) => {
    const iconClass = getCarTypeIcon(carType.name)

    carOptionsHTML += `
      <div class="col-md-4">
        <div class="car-option" data-car-type="${carType.name}" data-rate="${carType.rate_per_km}">
          <div class="car-icon">
            <i class="${iconClass}"></i>
          </div>
          <h6>${carType.display_name}</h6>
          ${tripType === "round-trip" ? `
            <div class="total-price mt-0">₹${carType.rate_per_km}/km</div>
            <div class="total-price" id="${carType.name}Price" style="display:none;">₹0</div>
            ` : `
            <div class="rate" style="display:none;">₹${carType.rate_per_km}/km</div>
            <div class="total-price mt-0" id="${carType.name}Price">₹0</div>
          `}
        </div>
      </div>
    `
  })

  carOptionsHTML += `</div>`
  pricingOptions.innerHTML = carOptionsHTML
  initCarTypeTooltips();


  // 🔹 Fetch available cars from backend & set tooltips dynamically
  fetch("/api/available-cars-by-type/")
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      document.querySelectorAll('.car-option').forEach(option => {
        const type = option.querySelector('h6')?.textContent.trim();
        const cars = data.data[type] || [];

        // Create tooltip text with new lines
        let tooltipText = "Available Car's :<br>";
        tooltipText += cars.length > 0 ? cars.join('<br>') : 'No cars available';

        // Set HTML tooltip content for Bootstrap
        option.setAttribute('data-bs-original-title', tooltipText);
        option.removeAttribute('title');
      });

      // Initialize Bootstrap tooltips with HTML enabled
      const tooltipTriggerList = [].slice.call(document.querySelectorAll('.car-option'));
      tooltipTriggerList.map(el => new bootstrap.Tooltip(el, { html: true }));
    }
  })
  .catch(err => console.error('Error fetching available cars:', err));



  // Re-attach event listeners to new car options
  attachCarOptionListeners()

  console.log(`✅ Built ${activeCarTypes.length} dynamic car options for ${tripType}`)
}

// Function to get appropriate icon for car type
function getCarTypeIcon(carTypeName) {
  const iconMap = {
    hatchback: "bi bi-car-front-fill",
    sedan: "bi bi-car-front",
    suv: "bi bi-truck",
    luxury: "bi bi-car-front",
    minivan: "bi bi-truck",
    compact: "bi bi-car-front-fill",
    muv: "bi bi-truck",
  }

  return iconMap[carTypeName.toLowerCase()] || "bi bi-car-front"
}

// Function to attach event listeners to car options
function attachCarOptionListeners() {
  const carOptions = document.querySelectorAll(".car-option")
  const confirmBtn = document.getElementById("confirmSelection")

  carOptions.forEach((option) => {
    option.addEventListener("click", function () {
      console.log("🚗 Car selected:", this.dataset.carType)

      carOptions.forEach((opt) => opt.classList.remove("selected"))
      this.classList.add("selected")

      const carType = this.dataset.carType
      const tripType = document.getElementById("tripType")?.value || "one-way"

      let selectedCarData

      if (tripType === "one-way") {
        const rate = Number.parseFloat(this.dataset.rate) || getCarTypeRates(carType).oneWayRate
        const totalPrice = calculatedDistance * rate

        selectedCarData = {
          type: carType,
          rate: rate,
          totalPrice: totalPrice,
          distance: calculatedDistance,
          tripType: "one-way",
        }
      } else if (tripType === "round-trip") {
        const minPrice = Number.parseFloat(this.dataset.minPrice) || 0
        const maxPrice = Number.parseFloat(this.dataset.maxPrice) || 0
        const rateRange = this.dataset.rate || "0-0"

        selectedCarData = {
          type: carType,
          rateRange: rateRange,
          minPrice: minPrice,
          maxPrice: maxPrice,
          distance: calculatedDistance,
          tripType: "round-trip",
        }
      }

      selectedCar = selectedCarData

      const selectedCarType = document.getElementById("selectedCarType")
      const selectedPrice = document.getElementById("selectedPrice")
      const selectedCarInfo = document.getElementById("selectedCarInfo")

      if (selectedCarType) selectedCarType.textContent = carType.charAt(0).toUpperCase() + carType.slice(1)

      if (selectedPrice) {
        if (tripType === "one-way") {
          document.getElementById("selectedCarPriceEle").style.display = "";          
          selectedPrice.innerHTML = `   
          ₹${selectedCarData.totalPrice.toLocaleString()}         
            <div class="mt-1">              
              <p class="allowance-text">> Toll Tax & Parking as per actual</p>
            </div>
          `;
        } else {
          // compute numberOfDays & driverAllowance for the alert
          let numberOfDays = 1;
          const pickupDate = document.getElementById("pickupDate")?.value;
          const dropoffDate = document.getElementById("dropoffDate")?.value;
          if (pickupDate && dropoffDate) {
            const pickup = new Date(pickupDate);
            const dropoff = new Date(dropoffDate);
            numberOfDays = Math.max(1, Math.ceil((dropoff - pickup) / (1000 * 60 * 60 * 24)));
          }
          const driverAllowance = numberOfDays * 300;
          document.getElementById("selectedCarPriceEle").style.display = "none";
          selectedPrice.innerHTML = `
            <div class="enhanced-driver-allowance">
              <p class="allowance-text">> Includes driver allowance (₹300/- per day):
              </p>
              <p class="allowance-details">
                <b>
                  <img width="28" height="28" src="https://img.icons8.com/windows/32/baby-calendar.png" alt="calendar"/>
                  ${numberOfDays} day${numberOfDays > 1 ? "s" : ""} • <i class="bi bi-currency-rupee"></i>${driverAllowance}
                </b>
              </p>
            </div>
            <p class="allowance-text">> Toll Tax & Parking as per actual</p>
            <p class="allowance-text">> <b>Note:</b> For round-trip bookings, the average distance must be at least <b>300 km/day.</b></p>
          `;
        }
      }

      if (selectedCarInfo) selectedCarInfo.style.display = "block"

      if (confirmBtn) confirmBtn.disabled = false

      console.log(`✅ Selected ${carType} for ${tripType}:`, selectedCarData)
    })
  })
}

// =====================================================
// 4. ANIMATION & VISUAL EFFECTS
// =====================================================

// Counter animation functionality
function animateCounters() {
  const counters = document.querySelectorAll(".stat-number")
  const duration = 2500
  const startTime = performance.now()

  counters.forEach((counter) => {
    const target = +counter.getAttribute("data-count")
    let lastValue = 0

    function update(currentTime) {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      const easedProgress = easeOutQuart(progress)
      const value = Math.floor(easedProgress * target)

      if (value !== lastValue) {
        counter.innerText = value.toLocaleString()
        lastValue = value
      }

      if (progress < 1) {
        requestAnimationFrame(update)
      } else {
        counter.innerText = target.toLocaleString()
      }
    }
    requestAnimationFrame(update)
  })
}

// Initialize scroll-based animations
function initializeScrollAnimations() {
  // Stats section animation
  const statsSection = document.querySelector(".stats-section")
  let hasAnimated = false

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !hasAnimated) {
          setTimeout(() => animateCounters(), 300)
          hasAnimated = true
          observer.unobserve(entry.target)
        }
      })
    },
    {
      threshold: 0.3,
      rootMargin: "50px 0px -50px 0px",
    },
  )

  if (statsSection) {
    observer.observe(statsSection)
  }

  // General animation observer
  const animationObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible")
          animationObserver.unobserve(entry.target)
        }
      })
    },
    {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    },
  )

  // Observe all animation elements
  document.querySelectorAll(".fade-in, .slide-in-left, .slide-in-right").forEach((el) => {
    animationObserver.observe(el)
  })
}

// Enhanced car animations
function initializeEnhancedCarAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1"
        entry.target.style.transform = "translateY(0)"
        observer.unobserve(entry.target)
      }
    })
  }, observerOptions)

  // Animate car cards
  const carCards = document.querySelectorAll(".enhanced-car-card")
  carCards.forEach((card, index) => {
    card.style.opacity = "0"
    card.style.transform = "translateY(30px)"
    card.style.transition = `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.1}s`
    observer.observe(card)
  })

  // Animate stat cards
  const statCards = document.querySelectorAll(".enhanced-stat-card")
  statCards.forEach((card, index) => {
    card.style.opacity = "0"
    card.style.transform = "translateY(20px)"
    card.style.transition = `all 0.5s ease ${index * 0.1}s`
    observer.observe(card)
  })
}

// Enhanced Lottie loader hiding function
function hideLottieLoader() {
    const lottieLoaderOverlay = document.getElementById("lottie-loader-overlay");

    if (!lottieLoaderOverlay) {
        console.log("ℹ️ Lottie loader element not found");
        return;
    }

    console.log("🎬 Hiding Lottie loader...");

    // Add fade-out class
    lottieLoaderOverlay.classList.add("fade-out");

    // Ensure it's hidden after the transition
    lottieLoaderOverlay.addEventListener("transitionend", () => {
        lottieLoaderOverlay.style.display = "none";
        console.log("✅ Lottie loader hidden successfully");
    }, { once: true });

    // Fallback in case transitionend doesn't fire
    setTimeout(() => {
        if (lottieLoaderOverlay.style.display !== "none") {
            lottieLoaderOverlay.style.display = "none";
            console.log("⚠️ Lottie loader force-hidden (fallback)");
        }
    }, 1500);
}


// =====================================================
// 5. NAVIGATION & SCROLLING
// =====================================================

// Enhanced smooth scrolling for navigation
function initializeNavigation() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const targetId = this.getAttribute("href")
      const target = document.querySelector(targetId)

      if (target) {
        let offset = 120
        if (window.innerWidth <= 991.98) {
          offset = 130
        }
        if (targetId === "#home" || targetId === "#home-anchor") {
          offset = window.innerWidth <= 991.98 ? 120 : 100
        }

        const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset
        window.scrollTo({
          top: targetPosition,
          behavior: "smooth",
        })

        // Focus on first input if it's the booking form
        if (targetId === "#booking-form") {
          setTimeout(() => {
            const firstInput = target.querySelector('input[type="text"], input[type="email"]')
            if (firstInput) firstInput.focus()
          }, 500)
        }
      }
    })
  })
}

// Breadcrumb functionality
function initializeBreadcrumbs() {
  const breadcrumbLinks = document.querySelectorAll(".breadcrumb-item a")

  breadcrumbLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      const href = this.getAttribute("href")

      if (href === "/" || href === "#home") {
        e.preventDefault()
        if (window.location.pathname === "/") {
          window.scrollTo({ top: 0, behavior: "smooth" })
        } else {
          window.location.href = "/"
        }
      }

      if (href.startsWith("/#")) {
        e.preventDefault()
        const targetId = href.substring(2)
        const targetElement = document.getElementById(targetId)
        if (targetElement) {
          targetElement.scrollIntoView({ behavior: "smooth", block: "start" })
        } else {
          window.location.href = href
        }
      }
    })

    // Keyboard navigation support
    link.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault()
        this.click()
      }
    })
  })
}

// =====================================================
// 6. FORM HANDLING & VALIDATION - UPDATED FOR ROUND-TRIP
// =====================================================

// Trip type toggle functionality with date-only for round-trip
function initializeTripTypeToggle() {
  const tripTypeButtons = document.querySelectorAll(".trip-type-option")
  const tripTypeInput = document.getElementById("tripType")
  const dropoffDateContainer = document.getElementById("dropoffDateContainer")
  const dropoffDateInput = document.getElementById("dropoffDate")
  const pickupDateInput = document.getElementById("pickupDate")
  const localRideInfo = document.querySelector(".local-ride-info") // ✅ new block

  // --- NEW: pickup/dropoff elements and parent rows we will show/hide ---
  const pickupInput  = document.getElementById("pickupLocation");
  const dropoffInput = document.getElementById("dropoffLocation");

  // containers we want to show/hide as a whole
  const locationRow  = pickupInput?.closest(".row");
  const datetimeRow  = pickupDateInput?.closest(".row");
  const calcRow      = document.getElementById("calculateBtn")?.closest(".mb-3");
  // ----------------------------------------------------------------------

  tripTypeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      tripTypeButtons.forEach((btn) => btn.classList.remove("active"))
      button.classList.add("active")

      const tripType = button.getAttribute("data-trip")
      tripTypeInput.value = tripType

      // Toggle round-trip minimum distance note
      const minDistanceNote = document.getElementById("roundTripMinDistanceNote")
      if (minDistanceNote) {
        if (tripType === "round-trip") {
          minDistanceNote.classList.remove("hidden")
        } else {
          minDistanceNote.classList.add("hidden")
        }
      }

      // Toggle distance modal classes
      document.querySelector('#distancePriceModal').classList.toggle('round-trip-trip', tripType === 'round-trip')

      if (tripType === "one-way") {
        // Hide local-ride banner if present
        if (localRideInfo) localRideInfo.style.display = "none";

        // show rows & button again
        if (locationRow) locationRow.style.display = "";
        if (datetimeRow) datetimeRow.style.display = "";
        if (calcRow)     calcRow.style.display     = "";

        // keep existing behavior for one-way date UI
        dropoffDateContainer.classList.remove("visible")
        dropoffDateContainer.classList.add("hidden")
        dropoffDateInput.removeAttribute("required")
        dropoffDateInput.value = ""

        if (pickupDateInput) {
          pickupDateInput.type = "datetime-local"
        }
      } else if (tripType === "round-trip") {
        // Hide local-ride banner if present
        if (localRideInfo) localRideInfo.style.display = "none";

        // show rows & button again
        if (locationRow) locationRow.style.display = "";
        if (datetimeRow) datetimeRow.style.display = "";
        if (calcRow)     calcRow.style.display     = "";

        // keep existing behavior for round-trip date UI
        dropoffDateContainer.classList.remove("hidden")
        dropoffDateContainer.classList.add("visible")
        dropoffDateInput.setAttribute("required", "required")

        // re-add required on visible fields
        if (pickupInput) pickupInput.setAttribute("required","required");
        if (dropoffInput) dropoffInput.setAttribute("required","required");
        if (pickupDateInput) pickupDateInput.setAttribute("required","required");
        if (dropoffDateInput) dropoffDateInput.setAttribute("required","required");

        if (pickupDateInput) {
          pickupDateInput.type = "date";
          if (pickupDateInput.value) {
            const dateOnly = pickupDateInput.value.split("T")[0];
            pickupDateInput.value = dateOnly;
          }
        }
        if (dropoffDateInput) {
          dropoffDateInput.type = "date";
          if (dropoffDateInput.value) {
            const dateOnly = dropoffDateInput.value.split("T")[0];
            dropoffDateInput.value = dateOnly;
          }
        }
      } else if (tripType === "local-ride") {
        // ✅ Local Ride: show info & hide all booking controls you don’t want
        if (localRideInfo) localRideInfo.style.display = "block";

        // hide entire rows and the calculate button row
        if (locationRow) locationRow.style.display = "none";
        if (datetimeRow) datetimeRow.style.display = "none";
        if (calcRow)     calcRow.style.display     = "none";

        // hide the return date column (keeps your fade anim)
        dropoffDateContainer.classList.add("hidden");

        // remove requireds and clear values so hidden fields don’t block anything
        if (pickupInput) pickupInput.removeAttribute("required");
        if (dropoffInput) dropoffInput.removeAttribute("required");
        if (pickupDateInput) pickupDateInput.removeAttribute("required");
        if (dropoffDateInput) dropoffDateInput.removeAttribute("required");

        if (pickupInput)  pickupInput.value = "";
        if (dropoffInput) dropoffInput.value = "";
        if (pickupDateInput)  pickupDateInput.value  = "";
        if (dropoffDateInput) dropoffDateInput.value = "";
      }

      // Refresh car pricing if needed (keep original behavior)
      if (calculatedDistance > 0 && tripType !== "local-ride") {
        updateCarPrices(calculatedDistance)
      }
    })
  })

  // Initialize with one-way selected (or local-ride if that's stored)
  dropoffDateContainer.classList.add("visible")
  setTimeout(() => {
    if (tripTypeInput.value === "one-way") {
      dropoffDateContainer.classList.remove("visible")
      dropoffDateContainer.classList.add("hidden")
      dropoffDateInput.removeAttribute("required")
    } else if (tripTypeInput.value === "local-ride") {
      // local ride initially selected: show info & hide rows/button
      if (localRideInfo) localRideInfo.style.display = "block";
      if (locationRow) locationRow.style.display = "none";
      if (datetimeRow) datetimeRow.style.display = "none";
      if (calcRow)     calcRow.style.display     = "none";
      dropoffDateContainer.classList.add('hidden');
      if (pickupInput) pickupInput.removeAttribute('required');
      if (dropoffInput) dropoffInput.removeAttribute('required');
      if (pickupDateInput) pickupDateInput.removeAttribute('required');
      if (dropoffDateInput) dropoffDateInput.removeAttribute('required');
    }
  }, 100)
}


// Quick select functionality for datetime inputs
function initializeQuickSelect() {
  const pickupQuickButtons = document.querySelectorAll(".quick-select-btn:not(.dropoff-quick)")
  const pickupInput = document.getElementById("pickupDate")

  pickupQuickButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const hours = Number.parseInt(this.getAttribute("data-hours"))
      const now = new Date()

      if (hours === 24) {
        now.setDate(now.getDate() + 1)
      } else {
        now.setHours(now.getHours() + hours)
      }

      pickupInput.value = formatDateTimeLocal(now)
      this.style.transform = "scale(0.95)"
      setTimeout(() => {
        this.style.transform = "scale(1)"
      }, 150)
    })
  })

  const dropoffQuickButtons = document.querySelectorAll(".dropoff-quick")
  const dropoffInput = document.getElementById("dropoffDate")

  dropoffQuickButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const days = Number.parseInt(this.getAttribute("data-days"))
      const pickupValue = pickupInput.value

      if (!pickupValue) {
        alert("Please select pickup date first")
        return
      }

      const pickupDate = new Date(pickupValue)
      pickupDate.setDate(pickupDate.getDate() + days)
      dropoffInput.value = formatDateTimeLocal(pickupDate)

      this.style.transform = "scale(0.95)"
      setTimeout(() => {
        this.style.transform = "scale(1)"
      }, 150)
    })
  })
}

// Enhanced form validation
function validateBookingForm(formData) {
  console.log("🔍 Validating form data:", formData)
  const errors = []

  if (!formData.name || formData.name.trim().length < 2) {
    errors.push("Name is required (minimum 2 characters)")
  }
  if (!formData.email || !formData.email.includes("@") || formData.email.trim().length < 5) {
    errors.push("Valid email address is required")
  }
  if (!formData.phone || formData.phone.trim().length < 10) {
    errors.push("Phone number is required (minimum 10 digits)")
  }
  if (!formData.pickupLocation || formData.pickupLocation.trim().length < 3) {
    errors.push("Pickup location is required")
  }
  if (!formData.dropoffLocation || formData.dropoffLocation.trim().length < 3) {
    errors.push("Drop-off location is required")
  }
  if (!formData.pickupDate) {
    errors.push("Pickup date and time is required")
  }
  if (!formData.carType) {
    errors.push("Car type selection is required")
  }
  if (!formData.totalPrice || formData.totalPrice <= 0) {
    errors.push("Price calculation is required")
  }
  if (!formData.distance || formData.distance <= 0) {
    errors.push("Distance calculation is required")
  }

  // Date validation
  if (formData.pickupDate) {
    const pickupDate = new Date(formData.pickupDate)
    const today = new Date()
    if (pickupDate < today) {
      errors.push("Pickup date and time cannot be in the past")
    }
  }

  if (formData.tripType === "round-trip") {
    if (!formData.dropoffDate) {
      errors.push("Drop-off date is required for round trips")
    } else {
      const pickupDate = new Date(formData.pickupDate)
      const dropoffDate = new Date(formData.dropoffDate)
      if (dropoffDate <= pickupDate) {
        errors.push("Drop-off date must be after pickup date")
      }
    }
  }

  if (errors.length > 0) {
    console.log("❌ Validation failed with errors:", errors)
    alert("Please fix the following issues:\n\n• " + errors.join("\n• "))
    return false
  }

  console.log("✅ Form validation passed")
  return true
}

// 🆕 NEW: Initialize booking form pre-fill from URL parameters
function initializeBookingFormPrefill() {
  console.log("🔗 Initializing booking form pre-fill...")

  // Get URL parameters
  const urlParams = getURLParameters()
  console.log("📋 URL Parameters found:", urlParams)

  // Check if we have origin and destination parameters
  if (urlParams.origin || urlParams.destination) {
    console.log("✅ Route parameters detected, pre-filling form...")

    // Pre-fill pickup location (origin)
    if (urlParams.origin) {
      const pickupLocationInput = document.getElementById("pickupLocation")
      if (pickupLocationInput) {
        pickupLocationInput.value = urlParams.origin
        console.log("📍 Pickup location set to:", urlParams.origin)

        // Add visual feedback
        pickupLocationInput.style.backgroundColor = "#e8f5e8"
        setTimeout(() => {
          pickupLocationInput.style.backgroundColor = ""
        }, 2000)
      }
    }

    // Pre-fill dropoff location (destination)
    if (urlParams.destination) {
      const dropoffLocationInput = document.getElementById("dropoffLocation")
      if (dropoffLocationInput) {
        dropoffLocationInput.value = urlParams.destination
        console.log("📍 Dropoff location set to:", urlParams.destination)

        // Add visual feedback
        dropoffLocationInput.style.backgroundColor = "#e8f5e8"
        setTimeout(() => {
          dropoffLocationInput.style.backgroundColor = ""
        }, 2000)
      }
    }

    // Show success notification
    showRoutePrefilledNotification(urlParams.origin, urlParams.destination)

    // Scroll to booking form after a short delay
    setTimeout(() => {
      const bookingForm = document.getElementById("booking-form")
      if (bookingForm) {
        bookingForm.scrollIntoView({ behavior: "smooth", block: "start" })
      }
    }, 1000)

    // Clean up URL (remove parameters from hash)
    if (window.location.hash.includes("?")) {
      const cleanHash = window.location.hash.split("?")[0]
      window.history.replaceState({}, document.title, window.location.pathname + cleanHash)
    }
  }
}

// 🆕 NEW: Show route pre-filled notification
function showRoutePrefilledNotification(origin, destination) {
  const notification = document.createElement("div")
  notification.className = "route-prefilled-notification"
  notification.innerHTML = `
    <div class="notification-content">
      <i class="bi bi-check-circle-fill"></i>
      <div class="notification-text">
        <strong>Route Pre-filled!</strong>
        <span>${origin} → ${destination}</span>
      </div>
    </div>
  `

  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => notification.classList.add("show"), 100)

  // Hide notification after 4 seconds
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 400)
  }, 4000)
}

// =====================================================
// 7. 🔄 ENHANCED DISTANCE CALCULATION & ROUTE INFO
// =====================================================

// Distance calculation using DistanceMatrix API
function calculateDistanceMatrix(pickup, dropoff) {
  return new Promise((resolve, reject) => {
    try {
      if (!window.google || !google.maps || !google.maps.DistanceMatrixService) {
        return reject(new Error("Google Maps JS not loaded"));
      }

      const service = new google.maps.DistanceMatrixService();

      service.getDistanceMatrix(
        {
          origins: [pickup],
          destinations: [dropoff],
          travelMode: google.maps.TravelMode.DRIVING,
          unitSystem: google.maps.UnitSystem.METRIC,
          drivingOptions: {
            departureTime: new Date(),
            trafficModel: google.maps.TrafficModel.BEST_GUESS,
          },
        },
        (response, status) => {
          try {
            if (status !== "OK") {
              return reject(new Error("DistanceMatrix failed: " + status));
            }
            const el = response?.rows?.[0]?.elements?.[0];
            if (!el || el.status !== "OK") {
              return reject(new Error("No route found: " + (el?.status || "UNKNOWN")));
            }

            const distanceKm = Number(el.distance?.value) / 1000; // meters → km
            const durationSec = Number((el.duration_in_traffic || el.duration)?.value);

            if (!Number.isFinite(distanceKm) || distanceKm <= 0) {
              return reject(new Error("Invalid distance from API"));
            }

            // Refresh the UI with the actual API duration if present
            updateRouteInformation(distanceKm, Number.isFinite(durationSec) ? durationSec : null);

            resolve({ distanceKm, durationSec: Number.isFinite(durationSec) ? durationSec : null });
          } catch (cbErr) {
            reject(cbErr);
          }
        }
      );
    } catch (err) {
      reject(err);
    }
  });
}


// Fallback distance calculation
function calculateDistancePlaceholder(pickup, dropoff) {
  try {
    const a = (pickup || "").trim().toLowerCase();
    const b = (dropoff || "").trim().toLowerCase();
    if (!a || !b) return 0;

    if (a === b) return 8; // same-city nudge so we never get 0

    // A tiny known-distance map (non-blocking fallback)
    const cityDistances = {
      "ahmedabad|surat": 265,
      "ahmedabad|mumbai": 525,
      "delhi|jaipur": 280,
      "delhi|agra": 230,
      "mumbai|pune": 150,
      "delhi|mumbai": 1450,
      "mumbai|surat": 280,
      "surat|mumbai": 280,
    };

    const key1 = `${a}|${b}`;
    const key2 = `${b}|${a}`;
    const exact =
      (cityDistances[key1] ?? cityDistances[key2] ?? null);

    if (Number.isFinite(exact)) return exact;

    // Loose heuristic based on name length difference (never throws)
    const heuristic = Math.max(40, Math.min(1200, Math.abs(a.length - b.length) * 60));
    return heuristic;
  } catch (_) {
    return 0;
  }
}

// Update route information display with dynamic content
function updateRouteInformation(distanceKm, durationSeconds) {
  const distanceEl = document.getElementById("calculatedDistance");
  const durationEl = document.getElementById("estimatedDuration");
  const routeTypeEl = document.getElementById("routeType");

  // Clear any previous "calculating…" placeholder updates
  if (routeInfoPlaceholderTimer) {
    clearTimeout(routeInfoPlaceholderTimer);
    routeInfoPlaceholderTimer = null;
  }

  // Distance text (don’t throw on bad values)
  let distanceText = "—";
  if (Number.isFinite(distanceKm) && distanceKm >= 0) {
    distanceText = `${distanceKm.toFixed(1)} km`;
  }
  if (distanceEl) distanceEl.textContent = distanceText;

  // Route type based on distance (falls back gracefully)
  let type = "Interstate Route";
  if (Number.isFinite(distanceKm)) {
    if (distanceKm < 100) type = "Intra-state / Short haul";
    else if (distanceKm < 400) type = "Interstate Route";
    else type = "Long-distance Route";
  }
  if (routeTypeEl) routeTypeEl.textContent = type;

  // ETA handling
  if (!durationEl) return;

  if (Number.isFinite(durationSeconds) && durationSeconds > 0) {
    durationEl.textContent = formatDuration(durationSeconds);
    durationEl.classList.remove("text-muted");
  } else {
    durationEl.textContent = "Calculating ETA…";
    durationEl.classList.add("text-muted");

    // After a brief moment, show a reasonable estimate based on distance
    routeInfoPlaceholderTimer = setTimeout(() => {
      const estSeconds = calculateEstimatedDuration(distanceKm);
      if (Number.isFinite(estSeconds) && estSeconds > 0) {
        durationEl.textContent = formatDuration(estSeconds) + " (estimated)";
      } else {
        durationEl.textContent = "ETA unavailable";
      }
      durationEl.classList.remove("text-muted");
      routeInfoPlaceholderTimer = null;
    }, 1200);
  }
}


// Calculate estimated duration based on distance
function calculateEstimatedDuration(distanceKm) {
  if (!Number.isFinite(distanceKm) || distanceKm <= 0) return 0;

  // Base speed assumption and congestion factor
  const baseSpeedKmph =
    distanceKm < 100 ? 45 : distanceKm < 400 ? 60 : 65; // short:city-ish, mid:interstate, long:highway
  const congestionFactor = 1.15; // small buffer

  const hours = (distanceKm / baseSpeedKmph) * congestionFactor;
  return Math.round(hours * 3600); // seconds
}

// Format duration from seconds to human readable format
function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return "—";
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);

  if (hrs <= 0) return `${mins} min`;
  if (mins === 0) return `${hrs} hr`;
  return `${hrs} hr ${mins} min`;
}

// Update car prices based on distance and trip type
function updateCarPrices(distance) {
  console.log("💰 Updating car prices with distance:", distance, "km")

  // Wait for car types to be loaded
  if (!isCarTypesLoaded) {
    console.log("⏳ Car types not loaded yet, waiting...")
    setTimeout(() => updateCarPrices(distance), 500)
    return
  }

  // Get trip type
  const tripType = document.getElementById("tripType")?.value || "one-way"

  // Get number of days for round-trip
  let numberOfDays = 1
  if (tripType === "round-trip") {
    const pickupDate = document.getElementById("pickupDate")?.value
    const dropoffDate = document.getElementById("dropoffDate")?.value

    if (pickupDate && dropoffDate) {
      const pickup = new Date(pickupDate)
      const dropoff = new Date(dropoffDate)
      numberOfDays = Math.max(1, Math.ceil((dropoff - pickup) / (1000 * 60 * 60 * 24)))
    }
  }

  // Update each car option with dynamic rates
  const carOptions = document.querySelectorAll(".car-option")
  carOptions.forEach((option) => {
    const carType = option.getAttribute("data-car-type")
    const rates = getCarTypeRates(carType)

    if (tripType === "one-way") {
      // ONE-WAY: Show fixed price
      const totalPrice = distance * rates.oneWayRate
      const roundedPrice = Math.round(totalPrice / 25) * 25;

      option.setAttribute("data-rate", rates.oneWayRate)

      const rateElement = option.querySelector(".rate")
      if (rateElement) {
        rateElement.textContent = `₹${rates.oneWayRate}/km`
      }

      const priceElement = option.querySelector(".total-price")
      if (priceElement) {
        priceElement.innerHTML = `₹${roundedPrice.toLocaleString()}`
      }

      console.log(`💰 One-way ${carType}: ₹${rates.oneWayRate}/km × ${distance}km = ₹${roundedPrice.toLocaleString()}`)
    } else if (tripType === "round-trip") {
      // ROUND-TRIP: Show price range with enhanced driver allowance
      const driverAllowance = numberOfDays * 300 // ₹300 per day
      const minTotalPrice = distance * rates.minRate + driverAllowance
      const maxTotalPrice = distance * rates.maxRate + driverAllowance

      option.setAttribute("data-rate", `${rates.minRate}-${rates.maxRate}`)
      option.setAttribute("data-min-price", minTotalPrice)
      option.setAttribute("data-max-price", maxTotalPrice)

      const rateElement = option.querySelector(".total-price")
      if (rateElement) {
        rateElement.textContent = `₹${rates.minRate}-₹${rates.maxRate}/km`
      }

  //     const priceElement = option.querySelector(".total-price")
  //     if (priceElement) {
  //       priceElement.innerHTML = `
  //   <div class="price-range">₹${minTotalPrice.toLocaleString()} – ₹${maxTotalPrice.toLocaleString()}</div>
  // `
  //     }

      console.log(
        `💰 Round-trip ${carType}: ₹${rates.minRate}-₹${rates.maxRate}/km × ${distance}km + ₹${driverAllowance} = ₹${minTotalPrice.toLocaleString()}-₹${maxTotalPrice.toLocaleString()}`,
      )
    }
  })
}

// --- Mini Map & Route Drawing ---
let routeMap, directionsService, directionsRenderer;

function initRouteMap() {
  if (!window.google || !google.maps) return;
  const el = document.getElementById("routeMap");
  if (!el) return;

  if (!routeMap) {
    routeMap = new google.maps.Map(el, {
      zoom: 6,
      center: { lat: 22.9734, lng: 78.6569 },
      mapTypeControl: false,
      streetViewControl: false,
    });

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
      suppressMarkers: false,
      preserveViewport: false,
    });
    directionsRenderer.setMap(routeMap);
  }
}

function drawRouteOnMap(pickup, dropoff) {
  try {
    if (!pickup || !dropoff) return;
    if (!window.google || !google.maps) return;

    // If Directions API is not enabled, this will be undefined; just bail quietly
    if (!google.maps.DirectionsService) {
      console.warn("Directions API is not enabled for this key.");
      return;
    }

    initRouteMap();

    directionsService.route(
      {
        origin: pickup,
        destination: dropoff,
        travelMode: google.maps.TravelMode.DRIVING,
      },
      (result, status) => {
        if (status === "OK") {
          directionsRenderer.setDirections(result);
        } else {
          console.warn("Route drawing failed:", status);
        }
      }
    );

    // Fix sizing when map is inside a newly opened modal
    setTimeout(() => {
      if (routeMap) google.maps.event.trigger(routeMap, "resize");
    }, 100);
  } catch (err) {
    console.warn("drawRouteOnMap error:", err);
  }
}


// =====================================================
// 8. BOOKING SYSTEM & MODAL MANAGEMENT - UPDATED WITH ROUND-TRIP SUPPORT
// =====================================================

// Car option selection with round-trip pricing support
function initializeDistanceCalculation() {
  const calculateBtn  = document.getElementById("calculateBtn");
  const modalElement  = document.getElementById("distancePriceModal");
  const confirmBtn    = document.getElementById("confirmSelection");

  if (!calculateBtn || !modalElement || !confirmBtn) {
    console.error("Required elements not found for distance calculation!");
    return;
  }

  // Modal instance
  currentModal = new window.bootstrap.Modal(modalElement, {
    backdrop: "static",
    keyboard: false,
  });

  console.log("✅ Distance calculation initialized");

  // Keep this so the map knows where to draw when shown
  modalElement.addEventListener("shown.bs.modal", () => {
    try {
      drawRouteOnMap(lastPickupText || "", lastDropoffText || "");
    } catch (e) {
      console.warn("Mini-map draw skipped:", e);
    }
  });

  // Calculate distance button click
  calculateBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    console.log("🔘 Calculate button clicked");

    const pickupLocation  = document.getElementById("pickupLocation")?.value?.trim();
    const dropoffLocation = document.getElementById("dropoffLocation")?.value?.trim();

    if (!pickupLocation || !dropoffLocation) {
      alert("Please enter both pickup and drop-off locations first.");
      return;
    }
    if (pickupLocation.length < 3 || dropoffLocation.length < 3) {
      alert("Please enter valid location names (at least 3 characters each).");
      return;
    }

    // time validations (unchanged)
    const pickupDate  = document.getElementById("pickupDate")?.value?.trim();
    const dropoffDate = document.getElementById("dropoffDate")?.value?.trim();
    const tripType    = document.getElementById("tripType")?.value || "one-way";

    if (tripType === "one-way") {
      if (!pickupDate) {
        alert("Please enter pickup time.");
        return;
      }
    } else if (tripType === "round-trip") {
      if (!pickupDate || !dropoffDate) {
        alert("Please enter both pickup time and drop-off time.");
        return;
      }
    }

    calculateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Calculating Distance...';
    calculateBtn.disabled = true;

    try {
      console.log("🔄 Starting distance calculation...");
      updateRouteInformation(0, null); // set “Calculating…” state

      // Distance Matrix (returns { distanceKm, durationSec })
      let distanceKm, durationSec;
      try {
        const { distanceKm: km, durationSec: sec } =
          await calculateDistanceMatrix(pickupLocation, dropoffLocation);
        distanceKm  = km;
        durationSec = sec;
        console.log("✅ API Distance:", { distanceKm, durationSec });
      } catch (apiError) {
        console.warn("⚠️ API failed, using fallback:", apiError);
        distanceKm = calculateDistancePlaceholder(pickupLocation, dropoffLocation);
        durationSec = null; // we don’t have ETA in fallback
        // update UI with fallback numbers
        updateRouteInformation(distanceKm, durationSec);
      }

      if (!distanceKm || distanceKm <= 0) {
        throw new Error("No distance returned");
      }

      // --- post-distance UI writes (safe, non-throwing) ---
      try {
        const puEl = document.getElementById("modalPickupLocation");
        if (puEl) puEl.textContent = pickupLocation;

        const doEl = document.getElementById("modalDropoffLocation");
        if (doEl) doEl.textContent = dropoffLocation;
      } catch (uiErr) {
        console.warn("Non-blocking UI write skipped:", uiErr);
      }

      // make these available to the mini map
      lastPickupText  = pickupLocation;
      lastDropoffText = dropoffLocation;

      // keep your pricing logic intact
      calculatedDistance = distanceKm;

      console.log("🔄 Refreshing car types before showing modal...");
      try {
        await refreshCarTypesForModal();
      } catch (x) {
        console.warn("refreshCarTypesForModal failed (continuing):", x);
      }

      // Show modal (map will draw in shown.bs.modal)
      currentModal?.show();

    } catch (error) {
      console.error("❌ Distance calculation error:", error);
      let msg = "Unable to calculate distance. ";
      if (error?.message?.includes("not a recognized location")) {
        msg =
          error.message +
          "\n\nSuggestions:\n• Check spelling of location names\n• Use full city names (e.g., 'Mumbai')\n• Include state name if needed (e.g., 'Rajkot, Gujarat')";
      } else if (error?.message?.includes("timed out")) {
        msg = "Connection timed out. Please check your internet connection and try again.";
      } else {
        msg += "Please check your internet connection and try again, or contact us for assistance.";
      }
      alert(msg);
    } finally {
      calculateBtn.innerHTML = '<i class="bi bi-calculator"></i> Calculate Distance & Price';
      calculateBtn.disabled = false;
    }
  });

  confirmBtn.addEventListener("click", handleBookingConfirmation);
  modalElement.addEventListener("hidden.bs.modal", handleModalClose);
}


// Handle booking confirmation with round-trip support
async function handleBookingConfirmation() {
  console.log("✅ Confirm booking clicked")

  if (isBookingInProgress || !selectedCar) {
    console.log("⚠️ Booking in progress or no car selected")
    return
  }

  isBookingInProgress = true
  const confirmBtn = document.getElementById("confirmSelection")

  const tripType = document.getElementById("tripType")?.value || "one-way"
  let finalPrice = 0

  if (tripType === "one-way") {
    finalPrice = selectedCar.totalPrice || 0
  } else if (tripType === "round-trip") {
    // For round-trip, use average of min and max for booking
    finalPrice = ((selectedCar.minPrice || 0) + (selectedCar.maxPrice || 0)) / 2
  }

  const formData = {
    name: document.getElementById("name")?.value?.trim() || "",
    email: document.getElementById("email")?.value?.trim() || "",
    phone: document.getElementById("phone")?.value?.trim() || "",
    tripType: tripType,
    pickupLocation: document.getElementById("pickupLocation")?.value?.trim() || "",
    dropoffLocation: document.getElementById("dropoffLocation")?.value?.trim() || "",
    pickupDate: document.getElementById("pickupDate")?.value || "",
    dropoffDate: document.getElementById("dropoffDate")?.value || "",
    carType: selectedCar?.type || "",
    totalPrice: finalPrice,
    distance: selectedCar?.distance || 0,
    specialRequests: document.getElementById("modalSpecialRequests")?.value?.trim() || "",
    timestamp: new Date().toISOString(),
  }

  if (!validateBookingForm(formData)) {
    isBookingInProgress = false
    return
  }

  if (confirmBtn) {
    confirmBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Submitting to Server...'
    confirmBtn.disabled = true
  }

  try {
    const backendResponse = await submitBookingRequest(formData)

    if (currentModal) {
      currentModal.hide()
    }

    setTimeout(() => {
      showEnhancedBookingSuccess({
        ...formData,
        bookingId: backendResponse.booking_id,
        backendData: backendResponse.data,
      })
      resetBookingForm()
    }, 300)
  } catch (error) {
    console.error("Booking submission error:", error)
    let errorMessage = "Sorry, there was an error processing your booking. "

    if (error.message.includes("Missing required fields") || error.message.includes("Validation failed")) {
      errorMessage = "Please fill in all required fields correctly and try again."
    } else if (error.message.includes("Invalid date") || error.message.includes("past")) {
      errorMessage = "Please check your date selections and try again."
    } else if (error.message.includes("network") || error.message.includes("fetch")) {
      errorMessage = "Network error. Please check your internet connection and try again."
    } else {
      errorMessage += "Please try again or contact us directly."
    }
    alert(errorMessage)
  } finally {
    if (confirmBtn) {
      confirmBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Complete Booking'
      confirmBtn.disabled = false
    }
    isBookingInProgress = false
  }
}

// Handle modal close
function handleModalClose() {
  console.log("🔄 Modal closed, resetting...")

  const carOptions = document.querySelectorAll(".car-option")
  carOptions.forEach((opt) => opt.classList.remove("selected"))

  const selectedCarInfo = document.getElementById("selectedCarInfo")
  const modalSpecialRequests = document.getElementById("modalSpecialRequests")
  const confirmBtn = document.getElementById("confirmSelection")

  if (selectedCarInfo) selectedCarInfo.style.display = "none"
  if (modalSpecialRequests) modalSpecialRequests.value = ""
  if (confirmBtn) confirmBtn.disabled = true

  selectedCar = null
  isBookingInProgress = false
}

// =====================================================
// 9. BACKEND API COMMUNICATION
// =====================================================

// Submit booking request to backend
async function submitBookingRequest(formData) {
  try {
    console.log("🚀 Submitting booking to backend:", formData)

    const backendData = {
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      tripType: formData.tripType,
      pickupLocation: formData.pickupLocation,
      dropoffLocation: formData.dropoffLocation,
      pickupDate: formData.pickupDate,
      dropoffDate: formData.dropoffDate || null,
      carType: formData.carType,
      totalPrice: Math.round(Number.parseFloat(formData.totalPrice) * 100) / 100,
      distance: Math.round(Number.parseFloat(formData.distance) * 100) / 100,
      specialRequests: formData.specialRequests || "",
    }

    console.log("📤 Mapped backend data:", backendData)

    const response = await fetch("/api/inquiry/create-booking/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify(backendData),
    })

    console.log("📡 Response status:", response.status)
    const data = await response.json()
    console.log("📊 Response data:", data)

    if (!response.ok) {
      if (data.details) {
        console.error("❌ Backend validation errors:", data.details)
        const errorMessages = []
        for (const [field, errors] of Object.entries(data.details)) {
          if (Array.isArray(errors)) {
            errorMessages.push(`${field}: ${errors.join(", ")}`)
          } else {
            errorMessages.push(`${field}: ${errors}`)
          }
        }
        throw new Error(`Validation failed:\n${errorMessages.join("\n")}`)
      }
      throw new Error(data.error || `Server responded with status ${response.status}`)
    }

    if (data.success) {
      console.log("✅ Booking submitted successfully:", data)
      return data
    } else {
      throw new Error(data.error || "Unknown error occurred")
    }
  } catch (error) {
    console.error("❌ Booking submission failed:", error)
    throw error
  }
}

// Check booking status
async function checkBookingStatus(bookingId) {
  try {
    const response = await fetch(`/api/inquiry/by-booking-id/?booking_id=${bookingId}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })

    const data = await response.json()
    if (data.success) {
      return data.data
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    console.error("Error checking booking status:", error)
    return null
  }
}

// =====================================================
// 10. UI COMPONENTS & INTERACTIONS
// =====================================================

// Car booking buttons functionality
function initializeCarBookingButtons() {
  const carBookButtons = document.querySelectorAll(".car-book-btn")

  carBookButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const carType = this.getAttribute("data-car-type")
      showCarSelectionNotification(carType)

      const bookingForm = document.getElementById("booking-form")
      if (bookingForm) {
        bookingForm.scrollIntoView({ behavior: "smooth", block: "start" })
      }
    })
  })
}

// Show car selection notification
function showCarSelectionNotification(carType) {
  const notification = document.getElementById("carSelectionNotification")
  const notificationText = document.getElementById("notificationText")

  if (notification && notificationText) {
    notificationText.textContent = `${carType.charAt(0).toUpperCase() + carType.slice(1)} selected! Complete your booking below.`
    notification.classList.add("show")
    setTimeout(() => notification.classList.remove("show"), 4000)
  }
}

// Enhanced car booking functionality
function initializeEnhancedCarBooking() {
  const bookButtons = document.querySelectorAll(".enhanced-book-btn:not(.unavailable)")

  bookButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const carType = this.getAttribute("data-car-type")
      const carName = this.getAttribute("data-car-name") || carType

      showEnhancedBookingNotification(carName, carType)

      const bookingForm = document.getElementById("booking-form")
      if (bookingForm) {
        setTimeout(() => {
          bookingForm.scrollIntoView({ behavior: "smooth", block: "start" })
        }, 1000)
      }
    })
  })
}

function showEnhancedBookingNotification(carName, carType) {
  const notification = document.createElement("div")
  notification.className = "enhanced-booking-notification"
  notification.innerHTML = `
    <div class="notification-content">
      <i class="bi bi-check-circle-fill"></i>
      <span>${carName} selected! Redirecting to booking form...</span>
    </div>
  `

  document.body.appendChild(notification)
  setTimeout(() => notification.classList.add("show"), 100)
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 400)
  }, 4000)
}

// 🆕 NEW: Initialize route booking buttons with pre-fill functionality
function initializeRouteBookingButtons() {
  console.log("🔗 Initializing route booking buttons...")

  // Handle service buttons in carousel (both index.html and popular-routes.html)
  const serviceButtons = document.querySelectorAll(".service-btn")

  serviceButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault()
      console.log("🚗 Route booking button clicked:", this.href)

      // Extract origin and destination from href
      const href = this.getAttribute("href")
      if (href && href.includes("?")) {
        const urlParams = new URLSearchParams(href.split("?")[1])
        const origin = urlParams.get("origin")
        const destination = urlParams.get("destination")

        if (origin && destination) {
          console.log("📍 Route detected:", origin, "→", destination)

          // If we're on the homepage, scroll to booking form and pre-fill
          if (window.location.pathname === "/" || window.location.pathname === "/index.html") {
            // Pre-fill the form directly
            prefillBookingForm(origin, destination)

            // Scroll to booking form
            setTimeout(() => {
              const bookingForm = document.getElementById("booking-form")
              if (bookingForm) {
                bookingForm.scrollIntoView({ behavior: "smooth", block: "start" })
              }
            }, 100)
          } else {
            // If we're on another page, redirect to homepage with parameters
            window.location.href = `/#booking-form?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`
          }
        }
      }
    })
  })

  console.log(`✅ Initialized ${serviceButtons.length} route booking buttons`)
}

// 🆕 NEW: Pre-fill booking form with route data
function prefillBookingForm(origin, destination) {
  console.log("📝 Pre-filling booking form with:", origin, "→", destination)

  // Pre-fill pickup location
  const pickupLocationInput = document.getElementById("pickupLocation")
  if (pickupLocationInput) {
    pickupLocationInput.value = origin
    pickupLocationInput.style.backgroundColor = "#e8f5e8"
    setTimeout(() => {
      pickupLocationInput.style.backgroundColor = ""
    }, 2000)
  }

  // Pre-fill dropoff location
  const dropoffLocationInput = document.getElementById("dropoffLocation")
  if (dropoffLocationInput) {
    dropoffLocationInput.value = destination
    dropoffLocationInput.style.backgroundColor = "#e8f5e8"
    setTimeout(() => {
      dropoffLocationInput.style.backgroundColor = ""
    }, 2000)
  }

  // Show success notification
  showRoutePrefilledNotification(origin, destination)
}

// 🆕 NEW: Initialize Our Cars page booking buttons
function initializeOurCarsBookingButtons() {
  console.log("🚗 Initializing Our Cars page booking buttons...")

  // Handle car booking buttons on our-cars.html page
  const carBookNowButtons = document.querySelectorAll(".car-book-now-btn")

  carBookNowButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault()
      console.log("🚗 Car Book Now button clicked")

      const carType = this.getAttribute("data-car-type")
      const carName = this.getAttribute("data-car-name") || carType
      const carId = this.getAttribute("data-car-id")

      console.log("📋 Car details:", { carType, carName, carId })

      // Show notification
      showCarBookingNotification(carName, carType)

      // Redirect to homepage booking form after a short delay
      setTimeout(() => {
        console.log("🔄 Redirecting to homepage booking form...")
        window.location.href = "/#booking-form"
      }, 1500)
    })
  })

  console.log(`✅ Initialized ${carBookNowButtons.length} car booking buttons`)
}

// 🆕 NEW: Show car booking notification for Our Cars page
function showCarBookingNotification(carName, carType) {
  const notification = document.getElementById("carSelectionNotification")
  const notificationText = document.getElementById("notificationText")

  if (notification && notificationText) {
    notificationText.textContent = `${carName} selected! Redirecting to booking form...`
    notification.classList.add("show")

    // Hide notification after redirect
    setTimeout(() => {
      notification.classList.remove("show")
    }, 2000)
  } else {
    // Create notification if it doesn't exist
    const newNotification = document.createElement("div")
    newNotification.className = "car-selection-notification show"
    newNotification.innerHTML = `
      <div class="notification-content">
        <i class="bi bi-check-circle-fill"></i>
        <span>${carName} selected! Redirecting to booking form...</span>
      </div>
    `

    document.body.appendChild(newNotification)

    // Remove notification after redirect
    setTimeout(() => {
      if (newNotification.parentNode) {
        newNotification.parentNode.removeChild(newNotification)
      }
    }, 2000)
  }
}
// DEDICATED FILTERING SCRIPT - GUARANTEED TO WORK
// Load this AFTER your main script.js

;(() => {
  // Wait for DOM to be fully ready
  function initializeFiltering() {
    // 1. Find filter buttons
    const filterButtons = document.querySelectorAll(".enhanced-filter-btn")

    // 2. Find items to filter
    const blogItems = document.querySelectorAll(".blog-item")
    const carItems = document.querySelectorAll(".enhanced-car-card")

    if (filterButtons.length === 0) {
      return
    }

    // 3. Set up click handlers
    filterButtons.forEach((button) => {
      button.addEventListener("click", function (e) {
        e.preventDefault()

        const filterValue = this.getAttribute("data-filter")

        // Remove active from all buttons
        filterButtons.forEach((btn) => btn.classList.remove("active"))

        // Add active to clicked button
        this.classList.add("active")

        let visibleCount = 0

        // Filter blog items
        blogItems.forEach((item) => {
          const category = item.getAttribute("data-category")
          const shouldShow = filterValue === "all" || category === filterValue

          if (shouldShow) {
            item.style.display = "block"
            visibleCount++
          } else {
            item.style.display = "none"
          }
        })

        // Filter car items
        carItems.forEach((item) => {
          const carType = item.getAttribute("data-car-type")
          const shouldShow = filterValue === "all" || carType === filterValue

          if (shouldShow) {
            item.style.display = "block"
            visibleCount++
          } else {
            item.style.display = "none"
          }
        })
      })
    })

    // 4. Auto-click "All" button
    const allButton = Array.from(filterButtons).find((btn) => btn.getAttribute("data-filter") === "all")
    if (allButton) {
      setTimeout(() => {
        allButton.click()
      }, 500)
    }
  }

  // Multiple initialization attempts
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeFiltering)
  } else {
    initializeFiltering()
  }

  // Backup initialization
  setTimeout(initializeFiltering, 1000)
  setTimeout(initializeFiltering, 3000)
})()

// =====================================================
// 11: GALLERY FUNCTIONS
// =====================================================

async function loadGalleryForIndex() {
  try {
    console.log("🖼️ Loading gallery images for index page...")

    const response = await fetch("/api/gallery-data/")
    const data = await response.json()

    if (data.status === "success" && data.data && data.data.length > 0) {
      const galleryGrid = document.getElementById("galleryGrid")
      const loadingText = document.querySelector(".gallery-loading")

      if (galleryGrid) {
        // Hide loading text if it exists
        if (loadingText) {
          loadingText.style.display = "none";
        }

        galleryGrid.style.cssText = `
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        grid-auto-rows: 250px;
        gap: 15px;
        padding: 0;
        max-width: 1200px;
        margin: 0 auto;
        `

        const imagesToShow = data.data.slice(0, 6)

        galleryGrid.innerHTML = imagesToShow
          .map((item, index) => {
            const spanClass = getGridSpanClass(index, imagesToShow.length)

            return `
              <div class="gallery-item ${spanClass}" style="
                position: relative;
                overflow: hidden;
                border-radius: 8px;
                cursor: pointer;
                background-color: #f8f9fa;
                transition: all 0.3s ease;
              " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 8px 25px rgba(0, 0, 0, 0.15)'" 
                 onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                ${item.video_url
                ? `
                <video controls preload="metadata" 
                      style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">
                  <source src="${item.video_url}" type="video/mp4">
                  Your browser does not support the video tag.
                </video>
                ` : `
                <img src="${item.image_url}" alt="${item.title}" loading="lazy" 
                    data-gallery-id="${item.id}"
                    style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;" 
                    onload="handleImageLoad(this)"
                    onmouseover="this.style.transform='scale(1.05)'" 
                    onmouseout="this.style.transform='scale(1)'" />
                `
                }
                <div class="gallery-overlay" style="
                  position: absolute;
                  bottom: 0;
                  left: 0;
                  right: 0;
                  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
                  color: white;
                  padding: 15px;
                  transform: translateY(100%);
                  transition: transform 0.3s ease;
                  border-radius: 0 0 8px 8px;
                " onmouseover="this.style.transform='translateY(0)'" 
                   onmouseout="this.style.transform='translateY(100%)'">
                  <h3 style="margin: 0 0 5px 0; font-size: 14px; font-weight: 600;">${item.title}</h3>
                  ${item.description ? `<p style="margin: 0; font-size: 12px; opacity: 0.9;">${item.description}</p>` : ""}
                </div>
              </div>
            `
          })
          .join("")

        const mediaQuery = window.matchMedia('(max-width: 768px)');
        const handleMobileLayout = (e) => {
          if (e.matches) {
            galleryGrid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(250px, 1fr))';
            galleryGrid.style.gap = '10px';
          } else {
            galleryGrid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
            galleryGrid.style.gap = '15px';
          }
        };
        if (mediaQuery.addEventListener) {
          mediaQuery.addEventListener('change', handleMobileLayout);
        } else {
          mediaQuery.addListener(handleMobileLayout); // fallback
        }
        handleMobileLayout(mediaQuery);

        console.log(`✅ Loaded ${imagesToShow.length} gallery images on index page`)
      }
    } else {
      console.log("ℹ️ No gallery images found for index page")
    }
  } catch (error) {
    console.error("❌ Error loading gallery for index:", error)
    const galleryGrid = document.getElementById("galleryGrid")
    const loadingText = document.querySelector(".gallery-loading")

    if (galleryGrid) {
      if (loadingText) {
        loadingText.innerHTML = `
        <div class="text-center py-4">
          <p class="text-muted">Unable to load gallery images at the moment.</p>
        </div>
        `;
      }
    }
  }
}

// ==== FULL GALLERY (Gallery page) ====

function setupGalleryFilters() {
  const filterButtons = document.querySelectorAll('.gallery-filter-btn');

  const applyFilter = (filter) => {
    // update active button state
    filterButtons.forEach(btn => {
      const btnFilter = (btn.getAttribute('data-filter') || '').toLowerCase().trim();
      btn.classList.toggle('active', btnFilter === filter);
    });

    // live-select items every time (handles dynamically added cards)
    document.querySelectorAll('.jg-item, .gallery-item').forEach(item => {
      const category = (item.getAttribute('data-category') || '').toLowerCase().trim();
      const show = filter === 'all' || category === filter;
      item.style.display = show ? 'block' : 'none';
      if (show) item.classList.add('fade-in');
    });
  };

  filterButtons.forEach(button => {
    button.addEventListener('click', function () {
      const filter = (this.getAttribute('data-filter') || 'all').toLowerCase().trim();
      applyFilter(filter);
    });
  });
}


async function loadGalleryForGalleryPage() {
  const grid = document.getElementById("galleryGrid");
  const loading = document.getElementById("galleryLoading");
  const empty = document.getElementById("galleryEmpty");
  if (!grid) return;

  // ensure correct base layout
  grid.classList.add("jg-grid");
  if (loading) loading.style.display = "block";
  if (empty) empty.style.display = "none";
  grid.innerHTML = "";

  try {
    const res = await fetch("/api/gallery-data/");
    const data = await res.json();

    const items = (data && data.status === "success" && Array.isArray(data.data)) ? data.data : [];

    if (!items.length) {
      if (loading) loading.style.display = "none";
      if (empty) empty.style.display = "block";
      return;
    }

    const frag = document.createDocumentFragment();

    items.forEach((item) => {
      const wrap = document.createElement("div");
      wrap.className = "jg-item";
      wrap.setAttribute("data-category", item.category || "all");

      // build card
      wrap.innerHTML = `
        <a href="${item.video_url ? item.video_url : item.image_url}" 
          data-fancybox="gallery" 
          data-caption="${item.title || ""}"
          ${item.video_url ? 'data-type="video"' : ''}>
          <article class="jg-card">
            <div class="jg-thumb">
              ${item.video_url
                ? `<video controls preload="metadata" style="width:100%; height:100%; object-fit:cover;" autoplay loop muted playsinline>
                    <source src="${item.video_url}" type="video/mp4">
                  </video>`
                : `<img src="${item.image_url}" alt="${item.title}" loading="lazy" />`
              }
            </div>
            <div class="jg-overlay">
              <h6 class="jg-title">${item.title || ""}</h6>
              ${item.description ? `<p class="jg-desc">${item.description}</p>` : ""}
            </div>
          </article>
        </a>
      `;
      frag.appendChild(wrap);
    });

    grid.appendChild(frag);

    if (loading) loading.style.display = "none";
    if (empty) empty.style.display = "none";

    // (re)bind filters after DOM is ready
    setupGalleryFilters();

  } catch (err) {
    console.error("Gallery load failed:", err);
    if (loading) loading.style.display = "none";
    if (empty) empty.style.display = "block";
  }
}


function handleImageLoad(img) {
  try {
    const aspectRatio = img.naturalWidth / img.naturalHeight;

    if (aspectRatio < 1.0) {
      const scale = Math.max(0.5, aspectRatio * 0.8);
      img.style.transform = `scale(${scale})`;
      img.style.objectFit = 'contain';
      img.style.backgroundColor = '#f8f9fa';
    } else if (aspectRatio < 1.3) {
      img.style.transform = 'scale(0.9)';
      img.style.objectFit = 'cover';
    } else {
      img.style.transform = 'scale(1)';
      img.style.objectFit = 'cover';
    }

    // Correctly read current scale
    const m = (img.style.transform || '').match(/scale\(([^)]+)\)/);
    const currentScale = m ? parseFloat(m[1]) : 1;
    const hoverScale = currentScale * 1.05;

    img.onmouseover = () => (img.style.transform = `scale(${hoverScale})`);
    img.onmouseout  = () => (img.style.transform = `scale(${currentScale})`);
  } catch (error) {
    console.error('Error in handleImageLoad:', error);
  }
}


function getGridSpanClass(index, totalImages) {
  // Create dynamic layout patterns based on image position
  const patterns = [
    "grid-span-1", // Normal size
    "grid-span-2", // Larger size (spans 2 rows)
    "grid-span-1", // Normal size
    "grid-span-wide", // Wide size (spans 2 columns)
    "grid-span-1", // Normal size
    "grid-span-1", // Normal size
  ]

  // Apply pattern based on index, with some randomization for variety
  const patternIndex = index % patterns.length
  return patterns[patternIndex]
}


// =====================================================
// 12. SUCCESS NOTIFICATIONS & FEEDBACK
// =====================================================

// Enhanced booking success function
function showEnhancedBookingSuccess(formData) {
  const modalId = "bookingSuccessModal_" + Date.now()
  const existingModals = document.querySelectorAll('[id^="bookingSuccessModal_"]')
  existingModals.forEach((modal) => modal.remove())

  const bookingId = formData.bookingId || `JTT${Date.now()}`

  const modalHTML = `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true" data-bs-backdrop="static">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content booking-success-modal">
          <div class="modal-header border-0 text-center">
            <div class="w-100">
              <div class="success-icon mb-3">
                <i class="bi bi-check-circle-fill"></i>
              </div>
              <h4 class="modal-title text-success" id="${modalId}Label">Booking Confirmed!</h4>
            </div>
          </div>
          <div class="modal-body text-center">
            <p class="lead mb-4">Your taxi booking has been successfully submitted and saved to our system.</p>
            
            <div class="booking-details">
              <div class="booking-id mb-3">
                <strong>Booking ID:</strong> <span class="text-primary">${bookingId}</span>
              </div>
              
              <div class="trip-details">
                <h6 class="mb-3">Trip Details:</h6>
                <div class="row text-start">
                  <div class="col-6"><strong>Name:</strong></div>
                  <div class="col-6">${formData.name}</div>
                  
                  <div class="col-6"><strong>Route:</strong></div>
                  <div class="col-6">${formData.pickupLocation} → ${formData.dropoffLocation}</div>
                  
                  <div class="col-6"><strong>Pickup:</strong></div>
                  <div class="col-6">${new Date(formData.pickupDate).toLocaleString()}</div>
                  
                  <div class="col-6"><strong>Car Type:</strong></div>
                  <div class="col-6">${formData.carType.charAt(0).toUpperCase() + formData.carType.slice(1)}</div>
                  
                  <div class="col-6"><strong>Estimated Price:</strong></div>
                  <div class="col-6">₹${formData.totalPrice.toLocaleString()}</div>
                  
                  <div class="col-6"><strong>Status:</strong></div>
                  <div class="col-6"><span class="badge bg-warning">Pending Confirmation</span></div>
                </div>
              </div>
            </div>
            
            <div class="contact-info mt-4">
              <p class="text-muted">
                <i class="bi bi-info-circle me-2"></i>
                Your booking has been saved with ID <strong>${bookingId}</strong>. 
                We will contact you shortly to confirm your booking details and provide the final quote.
              </p>
            </div>
          </div>
          <div class="modal-footer border-0 justify-content-center">
            <button type="button" class="btn btn-success btn-lg" data-bs-dismiss="modal">
              <i class="bi bi-telephone-fill me-2"></i>We'll Call You Soon
            </button>
          </div>
        </div>
      </div>
    </div>
  `

  document.body.insertAdjacentHTML("beforeend", modalHTML)
  const successModal = new window.bootstrap.Modal(document.getElementById(modalId))
  successModal.show()

  document.getElementById(modalId).addEventListener("hidden.bs.modal", function () {
    this.remove()
  })
}

// =====================================================
// 13. CAROUSEL & INTERACTIVE COMPONENTS - FIXED
// =====================================================

// 🔧 FIXED: Initialize Enhanced Services Carousel
function initializeServicesCarousel() {
  console.log("🎠 Initializing Services Carousel...")

  // Load Swiper CSS if not already loaded
  if (!document.querySelector('link[href*="swiper"]')) {
    const swiperCSS = document.createElement("link")
    swiperCSS.rel = "stylesheet"
    swiperCSS.href = "https://cdn.jsdelivr.net/npm/swiper@8/swiper-bundle.min.css"
    document.head.appendChild(swiperCSS)
    console.log("📦 Swiper CSS loaded")
  }

  // Load Swiper JS if not already loaded
  if (!window.Swiper) {
    const swiperJS = document.createElement("script")
    swiperJS.src = "https://cdn.jsdelivr.net/npm/swiper@8/swiper-bundle.min.js"
    swiperJS.onload = initSwiper
    document.head.appendChild(swiperJS)
    console.log("📦 Loading Swiper JS...")
  } else {
    initSwiper()
  }

  function initSwiper() {
    console.log("🔧 Initializing Swiper...")

    if (window.Swiper) {
      try {
        const servicesSwiper = new window.Swiper(".services-carousel", {
          // Slides configuration
          slidesPerView: 1,
          spaceBetween: 30,

          // Auto play
          autoplay: {
            delay: 4000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true,
          },

          // Pagination
          pagination: {
            el: ".services-pagination",
            clickable: true,
            dynamicBullets: true,
          },

          // Navigation
          navigation: {
            nextEl: ".services-button-next",
            prevEl: ".services-button-prev",
          },

          breakpoints: {
            640: {
              slidesPerView: 1,
              spaceBetween: 20,
              centeredSlides: true,
            },
            768: {
              slidesPerView: 2,
              spaceBetween: 30,
              centeredSlides: false,
            },
            1024: {
              slidesPerView: 3,
              spaceBetween: 30,
              centeredSlides: false,
            },
          },

          // Effects
          effect: "slide",
          speed: 600,
          loop: true,
          centeredSlides: true,

          // Events
          on: {
            init: () => {
              console.log("✅ Swiper initialized successfully")
              const slides = document.querySelectorAll(".enhanced-service-card")
              slides.forEach((slide, index) => {
                setTimeout(() => slide.classList.add("animate-in"), index * 200)
              })
            },
            slideChange: function () {
              const activeSlides = this.slides
              activeSlides.forEach((slide) => {
                const card = slide.querySelector(".enhanced-service-card")
                if (card) {
                  card.classList.remove("animate-in")
                  setTimeout(() => card.classList.add("animate-in"), 100)
                }
              })
            },
          },
        })

        // Store reference globally for debugging
        window.servicesSwiper = servicesSwiper

        // Pause autoplay on hover
        const carouselContainer = document.querySelector(".services-carousel-wrapper")
        if (carouselContainer) {
          carouselContainer.addEventListener("mouseenter", () => {
            servicesSwiper.autoplay.stop()
          })
          carouselContainer.addEventListener("mouseleave", () => {
            servicesSwiper.autoplay.start()
          })
        }

        console.log("🎠 Services carousel initialized successfully!")
      } catch (error) {
        console.error("❌ Error initializing Swiper:", error)
        fallbackToStaticGrid()
      }
    } else {
      console.warn("⚠️ Swiper library not found")
      fallbackToStaticGrid()
    }
  }

  function fallbackToStaticGrid() {
    console.log("🔄 Falling back to static grid layout...")

    const servicesWrapper = document.querySelector(".swiper-wrapper")
    if (servicesWrapper) {
      servicesWrapper.style.display = "grid"
      servicesWrapper.style.gridTemplateColumns = "repeat(auto-fit, minmax(300px, 1fr))"
      servicesWrapper.style.gap = "30px"
      servicesWrapper.style.transform = "none"
    }

    // Hide navigation and pagination
    const navigation = document.querySelector(".services-navigation")
    const pagination = document.querySelector(".services-pagination")
    if (navigation) navigation.style.display = "none"
    if (pagination) pagination.style.display = "none"

    console.log("✅ Static grid fallback applied")
  }
}

// =====================================================
// 14. FORM UTILITIES & HELPERS
// =====================================================

// Initialize booking form submission
function initializeBookingForm() {
  const bookingForm = document.getElementById("bookingForm")
  if (bookingForm) {
    bookingForm.addEventListener("submit", (e) => {
      e.preventDefault()
    })
  }
  console.log("Booking form initialized - submission handled via modal")
}

// Reset the booking form
function resetBookingForm() {
  const bookingForm = document.getElementById("bookingForm")
  if (bookingForm) {
    bookingForm.reset()
  }

  selectedCar = null
  calculatedDistance = 0
  updateCarPrices(0)

  const selectedCarInfo = document.getElementById("selectedCarInfo")
  if (selectedCarInfo) selectedCarInfo.style.display = "none"
}

// =====================================================
// 15. RESPONSIVE & ACCESSIBILITY UTILITIES
// =====================================================

// Handle responsive behavior
function handleEnhancedResponsiveChanges() {
  const carCards = document.querySelectorAll(".enhanced-car-card")
  const isMobile = window.innerWidth <= 768

  carCards.forEach((card) => {
    if (isMobile) {
      card.style.transform = "none"
    }
  })
}

// Keyboard navigation support
function addKeyboardSupport() {
  const prevBtn = document.querySelector(".services-button-prev")
  const nextBtn = document.querySelector(".services-button-next")

  if (prevBtn) {
    prevBtn.addEventListener("keyup", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault()
        if (window.servicesSwiper) {
          window.servicesSwiper.slidePrev()
        }
      }
    })
  }

  if (nextBtn) {
    nextBtn.addEventListener("keyup", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault()
        if (window.servicesSwiper) {
          window.servicesSwiper.slideNext()
        }
      }
    })
  }
}

// =====================================================
// 16. INITIALIZATION & EVENT LISTENERS - UPDATED
// =====================================================

// Main DOM Content Loaded Event
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Taxi Booking System - Frontend JavaScript Initialized")

  // Initialize Lottie loader
  hideLottieLoader();   // instead of initializeLottieLoader

  // PRIORITY: Load dynamic car types first with immediate refresh
  loadDynamicCarTypes().then(() => {
    console.log("🎯 Car types loaded, system ready for bookings")
  })

  // Load gallery images for index page
  const grid = document.getElementById("galleryGrid");
    if (grid) {
        const path = window.location.pathname || "";
        if (path.startsWith("/gallery")) {
            loadGalleryForGalleryPage();
        } else {
            loadGalleryForIndex();
        }
    }

  // Core functionality initialization
  initializeNavigation()
  initializeScrollAnimations()
  initializeTripTypeToggle()
  initializeDistanceCalculation()
  initializeBookingForm()
  initializeCarBookingButtons()
  initializeQuickSelect()
  initializeBreadcrumbs()

  // Enhanced features initialization
  initializeEnhancedCarBooking()
  initializeEnhancedCarAnimations()

  // 🆕 NEW: Route booking with pre-fill functionality
  initializeRouteBookingButtons()

  // 🆕 NEW: Initialize booking form pre-fill from URL parameters
  setTimeout(() => {
    initializeBookingFormPrefill()
  }, 500)

  // 🆕 NEW: Our Cars page booking buttons
  initializeOurCarsBookingButtons()

  // 🆕 NEW: Brand new filtering system
  // (Already initialized in the dedicated filtering script above)

  // 🔧 FIXED: Carousel initialization with proper delay
  setTimeout(() => {
    initializeServicesCarousel()
  }, 1500) // Increased delay to ensure DOM is fully ready

  // Responsive and accessibility
  addKeyboardSupport()
  handleEnhancedResponsiveChanges()

  console.log("✅ All systems initialized successfully")
})

// Window resize event
window.addEventListener("resize", handleEnhancedResponsiveChanges)

// =====================================================
// 17. CSS INJECTION FOR ANIMATIONS
// =====================================================

// Inject required CSS for animations and components
const requiredCSS = `
.enhanced-service-card {
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.enhanced-service-card.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.booking-success-modal .success-icon {
  font-size: 4rem;
  color: #28a745;
}

.booking-success-modal .booking-details {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 0.5rem;
  margin: 1rem 0;
}

.enhanced-booking-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
  z-index: 1050;
  transform: translateX(400px);
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 320px;
}

.enhanced-booking-notification.show {
  transform: translateX(0);
  opacity: 1;
}

.enhanced-booking-notification .notification-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 0.95rem;
}

.enhanced-booking-notification i {
  font-size: 1.25rem;
  animation: checkPulse 1.5s ease-out;
}

/* 🆕 NEW: Route pre-filled notification styles */
.route-prefilled-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #2a9d8f 0%, #53c0cb 100%);
  color: white;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(42, 157, 143, 0.3);
  z-index: 1050;
  transform: translateX(400px);
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 350px;
}

.route-prefilled-notification.show {
  transform: translateX(0);
  opacity: 1;
}

.route-prefilled-notification .notification-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 0.95rem;
}

.route-prefilled-notification .notification-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.route-prefilled-notification .notification-text strong {
  font-size: 1rem;
  font-weight: 700;
}

.route-prefilled-notification .notification-text span {
  font-size: 0.85rem;
  opacity: 0.9;
  font-weight: 500;
}

.route-prefilled-notification i {
  font-size: 1.25rem;
  animation: checkPulse 1.5s ease-out;
}

/* ✅ NEW: Enhanced route information styling */
.route-details .calculating {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes checkPulse {
  0% { transform: scale(0); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

@media (max-width: 768px) {
  .enhanced-booking-notification,
  .route-prefilled-notification {
    right: 10px;
    top: 10px;
    max-width: 280px;
    padding: 12px 16px;
  }
  
  .route-prefilled-notification .notification-content {
    font-size: 0.85rem;
  }
  
  .route-prefilled-notification .notification-text strong {
    font-size: 0.9rem;
  }
  
  .route-prefilled-notification .notification-text span {
    font-size: 0.8rem;
  }
}

/* Enhanced filter button animations */
.enhanced-filter-btn {
  transition: all 0.3s ease;
}

.enhanced-filter-btn.active {
  background-color: #2a9d8f !important;
  color: white !important;
  border-color: #2a9d8f !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(42, 157, 143, 0.3);
}

/* Smooth item transitions */
.blog-item, .enhanced-car-card {
  transition: all 0.3s ease;
}

/* 🔧 FIXED: Swiper carousel specific styles */
.services-carousel .swiper {
  overflow: visible;
}

.services-carousel .swiper-wrapper {
  align-items: stretch;
}

.services-carousel .swiper-slide {
  height: auto;
  display: flex;
}

.services-carousel .enhanced-service-card {
  width: 100%;
  height: 100%;
}

/* Navigation button improvements */
.services-button-prev,
.services-button-next {
  opacity: 0.8;
  transition: all 0.3s ease;
}

.services-button-prev:hover,
.services-button-next:hover {
  opacity: 1;
  transform: scale(1.1);
}

/* Pagination improvements */
.services-pagination .swiper-pagination-bullet {
  opacity: 0.5;
  transition: all 0.3s ease;
}

.services-pagination .swiper-pagination-bullet-active {
  opacity: 1;
  transform: scale(1.2);
}

/* ✅ NEW: Round-trip pricing styles */
.price-range {
  font-weight: bold;
  font-size: 0.9em;
  color: #2a9d8f;
}

.driver-allowance {
  color: #6c757d;
  font-style: italic;
  display: block;
  margin-top: 2px;
}

.car-option .total-price {
  text-align: center;
}

/* Date input styling for round-trip */
input[type="date"] {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 0.375rem;
  font-size: 1rem;
}

input[type="date"]:focus {
  border-color: #86b7fe;
  outline: 0;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

/* Trip type toggle styling */
.trip-type-toggle .trip-type-option.active {
  background-color: #2a9d8f;
  color: white;
  border-color: #2a9d8f;
}

/* Enhanced modal pricing display */
#selectedPrice small {
  display: block;
  margin-top: 4px;
  font-size: 0.85em;
  color: #6c757d;
}

/* Loading spinner for car types */
.spinner-border {
  width: 2rem;
  height: 2rem;
  border-width: 0.25em;
}

.spinner-border.text-primary {
  color: #2a9d8f !important;
}
`

// Inject CSS into document head
const styleSheet = document.createElement("style")
styleSheet.textContent = requiredCSS
document.head.appendChild(styleSheet)

// =====================================================
// 18. EXPORT UTILITIES (Optional)
// =====================================================

// === GOOGLE MAPS INITIALIZATION ===
window.initGoogle = function initGoogle() {
  try {
    setupPlacesAutocomplete();
    console.log("✅ Google Maps initialized");
  } catch (e) {
    console.warn("Google Maps init failed:", e);
  }
};

function setupPlacesAutocomplete() {
  if (!window.google || !google.maps || !google.maps.places) return;

  const commonOptions = {
    componentRestrictions: { country: "in" },
    fields: ["formatted_address", "geometry", "name"],
    types: ["(regions)"], // cities/states only
  };

  const pickupEl = document.getElementById("pickupLocation");
  const dropoffEl = document.getElementById("dropoffLocation");

  if (pickupEl) {
    const ac = new google.maps.places.Autocomplete(pickupEl, commonOptions);
    ac.addListener("place_changed", () => {
      const place = ac.getPlace();
      if (place && place.formatted_address) {
        pickupEl.value = place.formatted_address.replace(", India", "");
      }
    });
  }

  if (dropoffEl) {
    const ac = new google.maps.places.Autocomplete(dropoffEl, commonOptions);
    ac.addListener("place_changed", () => {
      const place = ac.getPlace();
      if (place && place.formatted_address) {
        dropoffEl.value = place.formatted_address.replace(", India", "");
      }
    });
  }
}


// Export utilities for potential external use
window.TaxiBookingSystem = {
  // Core functions
  calculateDistanceMatrix,
  calculateDistancePlaceholder,
  validateBookingForm,
  submitBookingRequest,

  // Dynamic car types functions
  loadDynamicCarTypes,
  getCarTypeRates,
  updateCarTypePricing,
  refreshCarTypesForModal,
  buildDynamicCarOptions,
  dynamicCarTypes: () => dynamicCarTypes,
  isCarTypesLoaded: () => isCarTypesLoaded,

  // Enhanced route information functions
  updateRouteInformation,
  calculateEstimatedDuration,
  formatDuration,

  // UI functions
  showEnhancedBookingSuccess,
  showCarSelectionNotification,

  // Route booking functions
  prefillBookingForm,
  showRoutePrefilledNotification,
  getURLParameters,

  // Our Cars booking functions
  initializeOurCarsBookingButtons,
  showCarBookingNotification,

  // State getters
  getSelectedCar: () => selectedCar,
  getCalculatedDistance: () => calculatedDistance,
  isBookingInProgress: () => isBookingInProgress,

  // Utility functions
  formatDateTimeLocal,
  getCSRFToken,
}

console.log("🎯 Taxi Booking System - All modules loaded and ready!")
console.log("🚗 Dynamic car types system initialized with round-trip pricing support!")
console.log("🗺️ Enhanced route information display with dynamic duration calculation!")

// =====================================================
// END OF TAXI BOOKING SYSTEM JAVASCRIPT
// =====================================================


// ====== Fancybox Integration for Gallery ======
document.addEventListener("DOMContentLoaded", function () {
    if (window.jQuery && $('[data-fancybox]').length) {
        $('[data-fancybox]').fancybox({
            buttons: ["fullScreen", "thumbs", "share", "slideShow", "close"],
            protect: true
        });
    }
});

