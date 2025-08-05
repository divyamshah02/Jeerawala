document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("bookingForm");
  if (!form) {
    console.warn("Booking form not found.");
    return;
  }

  console.log("Booking form initialized - ready to submit");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Get form values
    const data = {
      name: form.name.value,
      email: form.email.value,
      number: form.phone.value,
      origin: form.pickupLocation.value,
      destination: form.dropoffLocation.value,
      datetime: form.pickupDate.value,
      return_datetime: form.dropoffDate.value || null,
      trip_type: form.tripType.value,
      car_type: form.carType.value, // Car type ID (must match DB)
      distance_km: form.distance_km.value,
      price: form.price.value,
      special_requests: form.modalSpecialRequests.value || ""
    };

    try {
      const response = await fetch("/api/inquiry/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(), // Optional for dev
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        alert("✅ Booking submitted successfully!");
        form.reset();
      } else {
        const error = await response.json();
        console.error("❌ Booking failed:", error);
        alert("There was an error submitting your booking. Please check your details.");
      }
    } catch (err) {
      console.error("❌ Network error:", err);
      alert("Network error. Please check your connection or try again later.");
    }
  });

  // Optional: fetch car types dynamically (if you're using it later)
  /*
  fetch("/api/car-types/")
    .then(res => res.json())
    .then(data => console.log("Car types:", data))
    .catch(err => console.error("Failed to load car types:", err));
  */
});

function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}
