// Main JavaScript functionality
document.addEventListener("DOMContentLoaded", () => {
  // Auto-hide flash messages after 5 seconds
  const flashMessages = document.querySelectorAll(".flash-message")
  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.style.opacity = "0"
      setTimeout(() => {
        message.remove()
      }, 300)
    }, 5000)
  })

  const mobileMenuToggle = document.querySelector(".mobile-menu-toggle")
  const navLinks = document.querySelector(".nav-links")

  if (mobileMenuToggle && navLinks) {
    // Toggle mobile menu
    mobileMenuToggle.addEventListener("click", (e) => {
      e.stopPropagation()
      navLinks.classList.toggle("active")
      mobileMenuToggle.classList.toggle("active")
    })

    // Close mobile menu when clicking outside
    document.addEventListener("click", (e) => {
      if (!navLinks.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
        navLinks.classList.remove("active")
        mobileMenuToggle.classList.remove("active")
      }
    })

    // Close mobile menu when clicking on nav links
    const navLinksItems = navLinks.querySelectorAll(".nav-link")
    navLinksItems.forEach((link) => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("active")
        mobileMenuToggle.classList.remove("active")
      })
    })

    // Close mobile menu on window resize if screen becomes larger
    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) {
        navLinks.classList.remove("active")
        mobileMenuToggle.classList.remove("active")
      }
    })
  }

  // Form validation
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const requiredFields = form.querySelectorAll("[required]")
      let isValid = true

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          isValid = false
          field.style.borderColor = "var(--error-color)"
        } else {
          field.style.borderColor = "var(--border-color)"
        }
      })

      if (!isValid) {
        e.preventDefault()
        alert("Please fill in all required fields.")
      }
    })
  })
})

// Utility functions
function showLoading(button) {
  button.disabled = true
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...'
}

function hideLoading(button, originalText) {
  button.disabled = false
  button.innerHTML = originalText
}

function confirmDelete(message) {
  return confirm(message || "Are you sure you want to delete this item?")
}

// Date formatting
function formatDate(dateString) {
  const options = { year: "numeric", month: "long", day: "numeric" }
  return new Date(dateString).toLocaleDateString(undefined, options)
}

function calculateAge(birthDate) {
  const today = new Date()
  const birth = new Date(birthDate)
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--
  }

  return age
}
