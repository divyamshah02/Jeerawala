// js/script.js - UPDATED WITH CAR BOOKING REDIRECTION

// =====================================================
// TAXI BOOKING SYSTEM - FRONTEND JAVASCRIPT
// Restructured by Frontend Responsibilities
// =====================================================

// =====================================================
// 📋 TABLE OF CONTENTS / INDEX
// =====================================================
/*
┌─────────────────────────────────────────────────────────────────┐
│                    🚖 TAXI BOOKING SYSTEM                      │
│                     JavaScript Index                           │
└─────────────────────────────────────────────────────────────────┘

📍 SECTION 1: GLOBAL VARIABLES & CONFIGURATION (Line ~50)
   ├── Booking state management variables
   ├── API configuration constants
   └── System-wide settings

📍 SECTION 2: UTILITY FUNCTIONS (Line ~65)
   ├── easeOutQuart() - Animation easing function
   ├── formatDateTimeLocal() - Date formatting helper
   ├── getCSRFToken() - Security token retrieval
   └── 🆕 getURLParameters() - URL parameter parsing

📍 SECTION 3: ANIMATION & VISUAL EFFECTS (Line ~90)
   ├── animateCounters() - Stats counter animations
   ├── initializeScrollAnimations() - Scroll-based animations
   └── initializeEnhancedCarAnimations() - Car card animations

📍 SECTION 4: NAVIGATION & SCROLLING (Line ~180)
   ├── initializeNavigation() - Smooth scrolling setup
   └── initializeBreadcrumbs() - Breadcrumb navigation

📍 SECTION 5: FORM HANDLING & VALIDATION (Line ~240)
   ├── initializeTripTypeToggle() - Trip type selection
   ├── initializeQuickSelect() - Quick date selection
   ├── validateBookingForm() - Form validation logic
   └── 🆕 initializeBookingFormPrefill() - Pre-fill form from URL params

📍 SECTION 6: DISTANCE CALCULATION & API INTEGRATION (Line ~380)
   ├── calculateDistanceMatrix() - Primary API distance calculation
   ├── calculateDistancePlaceholder() - Fallback distance calculation
   └── updateCarPrices() - Price updates based on distance

📍 SECTION 7: BOOKING SYSTEM & MODAL MANAGEMENT (Line ~520)
   ├── initializeDistanceCalculation() - Distance calculation setup
   ├── handleBookingConfirmation() - Booking confirmation logic
   └── handleModalClose() - Modal cleanup

📍 SECTION 8: BACKEND API COMMUNICATION (Line ~720)
   ├── submitBookingRequest() - Backend booking submission
   └── checkBookingStatus() - Booking status verification

📍 SECTION 9: UI COMPONENTS & INTERACTIONS (Line ~820)
   ├── initializeCarBookingButtons() - Car selection buttons
   ├── initializeFilteringSystem() - 🆕 BRAND NEW FILTERING SYSTEM
   ├── initializeEnhancedCarBooking() - Enhanced car booking
   ├── 🆕 initializeRouteBookingButtons() - Route booking with prefill
   └── 🆕 initializeOurCarsBookingButtons() - NEW: Our Cars page booking

📍 SECTION 10: SUCCESS NOTIFICATIONS & FEEDBACK (Line ~950)
   └── showEnhancedBookingSuccess() - Success modal display

📍 SECTION 11: CAROUSEL & INTERACTIVE COMPONENTS (Line ~1050)
   └── initializeServicesCarousel() - 🔧 FIXED Swiper carousel setup

📍 SECTION 12: FORM UTILITIES & HELPERS (Line ~1150)
   ├── initializeBookingForm() - Form initialization
   └── resetBookingForm() - Form reset functionality

📍 SECTION 13: RESPONSIVE & ACCESSIBILITY UTILITIES (Line ~1180)
   ├── handleEnhancedResponsiveChanges() - Mobile responsiveness
   └── addKeyboardSupport() - Keyboard navigation

📍 SECTION 14: INITIALIZATION & EVENT LISTENERS (Line ~1220)
   └── Main DOM Content Loaded Event - System startup

📍 SECTION 15: CSS INJECTION FOR ANIMATIONS (Line ~1280)
   └── Dynamic CSS injection for animations

📍 SECTION 16: EXPORT UTILITIES (Line ~1350)
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

// API Configuration
const DISTANCE_MATRIX_API_KEY = "9rmBnCVMJAN8qPoxHROmBoNpXm4qQHPL5b6ttlnQbEzziHh28SSdBJ6zmNEZP1DI"
const API_TIMEOUT = 10000 // 10 seconds

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
// 3. ANIMATION & VISUAL EFFECTS
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
  const lottieLoaderOverlay = document.getElementById("lottie-loader-overlay")

  if (lottieLoaderOverlay) {
    console.log("🎬 Hiding Lottie loader...")

    // Check if already hidden
    if (lottieLoaderOverlay.style.display === "none" || lottieLoaderOverlay.classList.contains("fade-out")) {
      console.log("ℹ️ Lottie loader already hidden")
      return
    }

    // Add fade-out class
    lottieLoaderOverlay.classList.add("fade-out")

    // Hide after transition completes
    const handleTransitionEnd = () => {
      lottieLoaderOverlay.style.display = "none"
      console.log("✅ Lottie loader hidden successfully")
    }

    lottieLoaderOverlay.addEventListener("transitionend", handleTransitionEnd, { once: true })

    // Fallback: Force hide after 1 second if transition doesn't fire
    setTimeout(() => {
      if (lottieLoaderOverlay.style.display !== "none") {
        lottieLoaderOverlay.style.display = "none"
        console.log("⚠️ Lottie loader force-hidden (fallback)")
      }
    }, 1000)
  } else {
    console.log("ℹ️ Lottie loader element not found")
  }
}

// Initialize Lottie loader management with multiple triggers
function initializeLottieLoader() {
  console.log("🎬 Initializing Lottie loader management...")

  // Primary trigger: Hide after DOM is ready
  setTimeout(hideLottieLoader, 2000)

  // Secondary trigger: Hide on window load
  window.addEventListener("load", () => {
    setTimeout(hideLottieLoader, 500)
  })

  // Emergency fallback: Force hide after 5 seconds regardless
  setTimeout(() => {
    const lottieLoaderOverlay = document.getElementById("lottie-loader-overlay")
    if (lottieLoaderOverlay && lottieLoaderOverlay.style.display !== "none") {
      lottieLoaderOverlay.style.display = "none"
      console.log("🚨 Emergency: Lottie loader force-hidden")
    }
  }, 5000)

  // Additional trigger for pages that might load slowly
  document.addEventListener("readystatechange", () => {
    if (document.readyState === "complete") {
      setTimeout(hideLottieLoader, 1000)
    }
  })
}

// =====================================================
// 4. NAVIGATION & SCROLLING
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
// 5. FORM HANDLING & VALIDATION
// =====================================================

// Trip type toggle functionality
function initializeTripTypeToggle() {
  const tripTypeButtons = document.querySelectorAll(".trip-type-option")
  const tripTypeInput = document.getElementById("tripType")
  const dropoffDateContainer = document.getElementById("dropoffDateContainer")
  const dropoffDateInput = document.getElementById("dropoffDate")

  tripTypeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      tripTypeButtons.forEach((btn) => btn.classList.remove("active"))
      button.classList.add("active")

      const tripType = button.getAttribute("data-trip")
      tripTypeInput.value = tripType

      if (tripType === "one-way") {
        dropoffDateContainer.classList.remove("visible")
        dropoffDateContainer.classList.add("hidden")
        dropoffDateInput.removeAttribute("required")
        dropoffDateInput.value = ""
      } else {
        dropoffDateContainer.classList.remove("hidden")
        dropoffDateContainer.classList.add("visible")
        dropoffDateInput.setAttribute("required", "required")
      }
    })
  })

  // Initialize with one-way selected
  dropoffDateContainer.classList.add("visible")
  setTimeout(() => {
    if (tripTypeInput.value === "one-way") {
      dropoffDateContainer.classList.remove("visible")
      dropoffDateContainer.classList.add("hidden")
      dropoffDateInput.removeAttribute("required")
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
// 6. DISTANCE CALCULATION & API INTEGRATION
// =====================================================

// Distance calculation using DistanceMatrix API
async function calculateDistanceMatrix(origin, destination) {
  const url = `https://api.distancematrix.ai/maps/api/distancematrix/json?origins=${encodeURIComponent(
    origin,
  )}&destinations=${encodeURIComponent(destination)}&key=${DISTANCE_MATRIX_API_KEY}`

  console.log("🌐 API URL:", url)

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT)

    const response = await fetch(url, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    })

    clearTimeout(timeoutId)
    console.log("📡 API Response status:", response.status)

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`)
    }

    const data = await response.json()
    console.log("📊 API Response data:", data)

    if (
      data.rows &&
      data.rows.length > 0 &&
      data.rows[0].elements &&
      data.rows[0].elements.length > 0 &&
      data.rows[0].elements[0].status === "OK"
    ) {
      const distanceInMeters = data.rows[0].elements[0].distance.value
      const distanceKm = distanceInMeters / 1000
      console.log("✅ Distance (km):", distanceKm)
      return distanceKm
    } else {
      console.warn("⚠️ DistanceMatrix response error:", data)
      throw new Error("Invalid API response")
    }
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Request timed out")
    }
    console.error("❌ Failed to fetch distance from DistanceMatrix.ai:", error)
    throw error
  }
}

// Fallback distance calculation
function calculateDistancePlaceholder(pickup, dropoff) {
  const validIndianLocations = [
    "mumbai",
    "delhi",
    "bangalore",
    "hyderabad",
    "ahmedabad",
    "chennai",
    "kolkata",
    "pune",
    "jaipur",
    "lucknow",
    "kanpur",
    "nagpur",
    "indore",
    "thane",
    "bhopal",
    "visakhapatnam",
    "pimpri",
    "patna",
    "vadodara",
    "ghaziabad",
    "ludhiana",
    "agra",
    "nashik",
    "faridabad",
    "meerut",
    "rajkot",
    "kalyan",
    "vasai",
    "varanasi",
    "srinagar",
    "aurangabad",
    "dhanbad",
    "amritsar",
    "navi mumbai",
    "allahabad",
    "ranchi",
    "howrah",
    "coimbatore",
    "jabalpur",
    "gwalior",
    "vijayawada",
    "jodhpur",
    "madurai",
    "raipur",
    "kota",
    "guwahati",
    "chandigarh",
    "solapur",
    "hubli",
    "bareilly",
    "moradabad",
    "mysore",
    "gurgaon",
    "aligarh",
    "jalandhar",
    "tiruchirappalli",
    "bhubaneswar",
    "salem",
    "warangal",
    "mira",
    "thiruvananthapuram",
    "bhiwandi",
    "saharanpur",
    "gorakhpur",
    "guntur",
    "bikaner",
    "amravati",
    "noida",
    "jamshedpur",
    "bhilai",
    "cuttack",
    "firozabad",
    "kochi",
    "bhavnagar",
    "dehradun",
    "durgapur",
    "asansol",
    "nanded",
    "kolhapur",
    "ajmer",
    "gulbarga",
    "jamnagar",
    "ujjain",
    "loni",
    "siliguri",
    "jhansi",
    "ulhasnagar",
    "nellore",
    "jammu",
    "sangli",
    "belgaum",
    "mangalore",
    "ambattur",
    "tirunelveli",
    "malegaon",
    "gaya",
    "jalgaon",
    "udaipur",
    "maheshtala",
    "surat",
  ]

  const pickupLower = pickup.toLowerCase()
  const dropoffLower = dropoff.toLowerCase()

  const pickupValid = validIndianLocations.some((city) => pickupLower.includes(city))
  const dropoffValid = validIndianLocations.some((city) => dropoffLower.includes(city))

  if (!pickupValid || !dropoffValid) {
    throw new Error("Please enter valid Indian city names for both pickup and drop-off locations.")
  }

  const cityDistances = {
    "mumbai-delhi": 1400,
    "mumbai-pune": 150,
    "mumbai-ahmedabad": 530,
    "mumbai-bangalore": 980,
    "delhi-mumbai": 1400,
    "delhi-jaipur": 280,
    "delhi-agra": 230,
    "delhi-chandigarh": 250,
    "pune-mumbai": 150,
    "pune-bangalore": 840,
    "ahmedabad-mumbai": 530,
    "ahmedabad-delhi": 950,
    "ahmedabad-surat": 273,
    "surat-ahmedabad": 273,
    "bangalore-chennai": 350,
    "bangalore-mumbai": 980,
    "bangalore-pune": 840,
    "chennai-bangalore": 350,
    "chennai-mumbai": 1340,
    "kolkata-delhi": 1470,
    "hyderabad-bangalore": 570,
    "hyderabad-chennai": 630,
  }

  const key1 =
    pickup.toLowerCase().replace(/\s+/g, "").replace(/,.*/, "") +
    "-" +
    dropoff.toLowerCase().replace(/\s+/g, "").replace(/,.*/, "")
  const key2 =
    dropoff.toLowerCase().replace(/\s+/g, "").replace(/,.*/, "") +
    "-" +
    pickup.toLowerCase().replace(/\s+/g, "").replace(/,.*/, "")

  return cityDistances[key1] || cityDistances[key2] || Math.floor(Math.random() * 600) + 100
}

// Update car prices based on distance
function updateCarPrices(distance) {
  const rates = { hatchback: 12, sedan: 15, suv: 18 }

  Object.keys(rates).forEach((carType) => {
    const price = distance * rates[carType]
    const priceElement = document.getElementById(carType + "Price")
    if (priceElement) {
      priceElement.textContent = "₹" + price.toLocaleString()
    }
  })
}

// =====================================================
// 7. BOOKING SYSTEM & MODAL MANAGEMENT
// =====================================================

// Initialize distance calculation functionality
function initializeDistanceCalculation() {
  const calculateBtn = document.getElementById("calculateBtn")
  const modalElement = document.getElementById("distancePriceModal")
  const carOptions = document.querySelectorAll(".car-option")
  const confirmBtn = document.getElementById("confirmSelection")

  if (!calculateBtn || !modalElement || !confirmBtn) {
    console.error("Required elements not found for distance calculation!")
    return
  }

  currentModal = new window.bootstrap.Modal(modalElement, {
    backdrop: "static",
    keyboard: false,
  })

  console.log("✅ Distance calculation initialized")

  // Calculate distance button click
  calculateBtn.addEventListener("click", async (e) => {
    e.preventDefault()
    console.log("🔘 Calculate button clicked")

    const pickupLocation = document.getElementById("pickupLocation")?.value?.trim()
    const dropoffLocation = document.getElementById("dropoffLocation")?.value?.trim()

    if (!pickupLocation || !dropoffLocation) {
      alert("Please enter both pickup and drop-off locations first.")
      return
    }

    if (pickupLocation.length < 3 || dropoffLocation.length < 3) {
      alert("Please enter valid location names (at least 3 characters each).")
      return
    }

    calculateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Calculating Distance...'
    calculateBtn.disabled = true

    try {
      console.log("🔄 Starting distance calculation...")
      let distanceKm

      try {
        distanceKm = await calculateDistanceMatrix(pickupLocation, dropoffLocation)
        console.log("✅ API Distance:", distanceKm)
      } catch (apiError) {
        console.warn("⚠️ API failed, using fallback:", apiError)
        distanceKm = calculateDistancePlaceholder(pickupLocation, dropoffLocation)
        console.log("✅ Fallback Distance:", distanceKm)
      }

      if (distanceKm && distanceKm > 0) {
        const modalPickup = document.getElementById("modalPickupLocation")
        const modalDropoff = document.getElementById("modalDropoffLocation")
        const modalDistance = document.getElementById("calculatedDistance")

        if (modalPickup) modalPickup.textContent = pickupLocation
        if (modalDropoff) modalDropoff.textContent = dropoffLocation
        if (modalDistance) modalDistance.textContent = `${distanceKm.toFixed(1)} km`

        calculatedDistance = distanceKm
        updateCarPrices(distanceKm)
        console.log("✅ Showing modal...")
        currentModal.show()
      } else {
        throw new Error("Unable to calculate distance")
      }
    } catch (error) {
      console.error("❌ Distance calculation error:", error)
      let errorMessage = "Unable to calculate distance. "

      if (error.message.includes("not a recognized location")) {
        errorMessage =
          error.message +
          "\n\nSuggestions:\n• Check spelling of location names\n• Use full city names (e.g., 'Mumbai' instead of 'Mum')\n• Include state name if needed (e.g., 'Rajkot, Gujarat')"
      } else if (error.message.includes("timed out")) {
        errorMessage = "Connection timed out. Please check your internet connection and try again."
      } else {
        errorMessage += "Please check your internet connection and try again, or contact us for assistance."
      }
      alert(errorMessage)
    } finally {
      calculateBtn.innerHTML = '<i class="bi bi-calculator"></i> Calculate Distance & Price'
      calculateBtn.disabled = false
    }
  })

  // Car option selection
  carOptions.forEach((option) => {
    option.addEventListener("click", function () {
      console.log("🚗 Car selected:", this.dataset.carType)

      carOptions.forEach((opt) => opt.classList.remove("selected"))
      this.classList.add("selected")

      const carType = this.dataset.carType
      const rate = Number.parseInt(this.dataset.rate)
      const totalPrice = calculatedDistance * rate

      selectedCar = {
        type: carType,
        rate: rate,
        totalPrice: totalPrice,
        distance: calculatedDistance,
      }

      const selectedCarType = document.getElementById("selectedCarType")
      const selectedPrice = document.getElementById("selectedPrice")
      const selectedCarInfo = document.getElementById("selectedCarInfo")

      if (selectedCarType) selectedCarType.textContent = carType.charAt(0).toUpperCase() + carType.slice(1)
      if (selectedPrice) selectedPrice.textContent = "₹" + totalPrice.toLocaleString()
      if (selectedCarInfo) selectedCarInfo.style.display = "block"

      confirmBtn.disabled = false
    })
  })

  confirmBtn.addEventListener("click", handleBookingConfirmation)
  modalElement.addEventListener("hidden.bs.modal", handleModalClose)
}

// Handle booking confirmation
async function handleBookingConfirmation() {
  console.log("✅ Confirm booking clicked")

  if (isBookingInProgress || !selectedCar) {
    console.log("⚠️ Booking in progress or no car selected")
    return
  }

  isBookingInProgress = true
  const confirmBtn = document.getElementById("confirmSelection")

  const formData = {
    name: document.getElementById("name")?.value?.trim() || "",
    email: document.getElementById("email")?.value?.trim() || "",
    phone: document.getElementById("phone")?.value?.trim() || "",
    tripType: document.getElementById("tripType")?.value || "one-way",
    pickupLocation: document.getElementById("pickupLocation")?.value?.trim() || "",
    dropoffLocation: document.getElementById("dropoffLocation")?.value?.trim() || "",
    pickupDate: document.getElementById("pickupDate")?.value || "",
    dropoffDate: document.getElementById("dropoffDate")?.value || "",
    carType: selectedCar?.type || "",
    totalPrice: selectedCar?.totalPrice || 0,
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
// 8. BACKEND API COMMUNICATION
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
// 9. UI COMPONENTS & INTERACTIONS
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
// 10. SUCCESS NOTIFICATIONS & FEEDBACK
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
// 11. CAROUSEL & INTERACTIVE COMPONENTS - FIXED
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

          // Responsive breakpoints
          breakpoints: {
            640: {
              slidesPerView: 1,
              spaceBetween: 20,
            },
            768: {
              slidesPerView: 2,
              spaceBetween: 30,
            },
            1024: {
              slidesPerView: 3,
              spaceBetween: 30,
            },
          },

          // Effects
          effect: "slide",
          speed: 600,
          loop: true,
          centeredSlides: false,

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
// 12. FORM UTILITIES & HELPERS
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
// 13. RESPONSIVE & ACCESSIBILITY UTILITIES
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
// 14. INITIALIZATION & EVENT LISTENERS
// =====================================================

// Main DOM Content Loaded Event
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Taxi Booking System - Frontend JavaScript Initialized")

  // FIRST: Initialize Lottie loader management
  initializeLottieLoader()

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
// 15. CSS INJECTION FOR ANIMATIONS
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
`

// Inject CSS into document head
const styleSheet = document.createElement("style")
styleSheet.textContent = requiredCSS
document.head.appendChild(styleSheet)

// =====================================================
// 16. EXPORT UTILITIES (Optional)
// =====================================================

// Export utilities for potential external use
window.TaxiBookingSystem = {
  // Core functions
  calculateDistanceMatrix,
  calculateDistancePlaceholder,
  validateBookingForm,
  submitBookingRequest,

  // UI functions
  showEnhancedBookingSuccess,
  showCarSelectionNotification,

  // 🆕 NEW: Route booking functions
  prefillBookingForm,
  showRoutePrefilledNotification,
  getURLParameters,

  // 🆕 NEW: Our Cars booking functions
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

// =====================================================
// END OF TAXI BOOKING SYSTEM JAVASCRIPT
// =====================================================
