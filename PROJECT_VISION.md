# PROJECT VISION

# Mosque Discovery & Prayer Information Platform

## Mission

The purpose of this platform is to help Muslims quickly discover nearby mosques, view prayer-related information, and find accurate jamaat timings wherever they are.

The platform is designed for both local residents and travelers who may be unfamiliar with a city and need reliable information about nearby mosques.

The system should prioritize simplicity, accessibility, accuracy, trust, and ease of use.

---

# Core Problem

When a Muslim enters a new city, they often face several challenges:

* They do not know where the nearest mosque is located.
* They do not know when the mosque's jamaat prayer starts.
* They do not know whether women are accommodated.
* They do not know whether the mosque is currently open.
* They do not know the mosque's facilities or special events.

While general prayer times are publicly available, mosque-specific jamaat timings are often difficult to find.

This platform aims to solve these problems.

---

# Target Audience

## Public Users

Any Muslim seeking mosque information.

Examples:

* Travelers
* Students
* Workers
* Tourists
* Local residents

Public users should not be required to create an account.

The platform should remain accessible without login.

---

## Mosque Administrators

Authorized representatives of verified mosques.

Responsibilities:

* Update jamaat timings.
* Update mosque opening and closing schedules.
* Upload mosque photos.
* Publish event announcements.
* Update women prayer availability.
* Maintain accurate mosque information.

Each mosque administrator may only manage their own mosque.

---

## Platform Owners

Platform owners manage and moderate the entire system.

Responsibilities:

* Review mosque registration requests.
* Verify mosque authenticity.
* Approve or reject requests.
* Create mosque administrator accounts.
* Monitor platform activity.
* Maintain data quality and trust.

Only platform owners may approve mosques.

---

# Platform Principles

## Accuracy

Information must be accurate and verified.

Mosques should not become public until approved.

---

## Simplicity

Many mosque administrators may not be highly technical.

The interface should:

* Be mobile friendly.
* Be easy to understand.
* Require minimal training.

---

## Accessibility

The platform should work well:

* On mobile phones.
* On slow internet connections.
* In rural and urban areas.

---

## Trust

Users should trust the information displayed.

Verification workflows should prevent:

* Fake mosques.
* Spam submissions.
* Incorrect information.

---

# User Journey

## Public User

1. Open website.
2. Allow location access.
3. System obtains location.
4. System calculates nearest mosques.
5. Display nearest mosques sorted by distance.
6. User selects mosque.
7. View:

   * Jamaat timings
   * Prayer information
   * Women prayer availability
   * Opening hours
   * Photos
   * Events
   * Directions

---

## Mosque Registration Flow

1. Mosque representative submits registration request.
2. Request enters pending review state.
3. Platform owner reviews request.
4. Platform owner approves or rejects request.
5. Approved requests create a mosque profile.
6. Mosque administrator account is created.
7. Login credentials are issued.
8. Mosque becomes publicly visible.

---

# Future Authentication Strategy

Public users:

* No login required.

Mosque administrators:

* Mobile number login.
* Password login.
* OTP support in future releases.

Platform owners:

* Secure administrator authentication.
* Strong password requirements.
* Multi-factor authentication in future.

---

# Prayer Time Strategy

The platform separates:

## Official Prayer Times

Calculated city prayer times.

Examples:

* Fajr
* Dhuhr
* Asr
* Maghrib
* Isha

These are city-level prayer times.

---

## Jamaat Times

Mosque-specific congregation times.

Examples:

* Fajr Jamaat: 5:15 AM
* Dhuhr Jamaat: 1:45 PM

Managed by mosque administrators.

---

# Mosque Information

Each mosque may contain:

* Name
* Address
* City
* Latitude
* Longitude
* Contact information
* Opening hours
* Closing hours
* Women prayer availability
* Photos
* Events
* Verification status

---

# GPS & Distance Discovery

The platform should use geolocation.

Users may allow location access.

The system should:

1. Obtain coordinates.
2. Calculate distance to nearby mosques.
3. Sort nearest to farthest.
4. Display top nearby mosques.

Distance calculations should be accurate and efficient.

---

# Long-Term Vision

The long-term goal is to build a trusted mosque discovery platform that helps Muslims worldwide find verified mosques and reliable prayer information.

The platform should remain:

* Community-driven
* Mobile-first
* Easy to use
* Secure
* Scalable
* Accurate

Every feature added to the project should support this mission.
