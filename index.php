<?php
// index.php
session_start();

// Check for cooldown message
$cooldown_seconds = 0;
if (isset($_SESSION['cooldown'])) {
    $remaining_time = $_SESSION['cooldown'] - time();
    if ($remaining_time > 0) {
        $cooldown_seconds = $remaining_time;
    } else {
        unset($_SESSION['cooldown']);
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>OpenStreetMap Business Scraper</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* General Styles */
        body {
            font-family: Arial, sans-serif;
            background-color: #f7f7f7;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background-color: #fff;
            padding: 20px;
            box-sizing: border-box;
            box-shadow: 0 0 10px #ccc;
        }
        h1, h2, p {
            text-align: center;
        }
        /* Form Styles */
        .form-group {
            margin-bottom: 15px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
        }
        label {
            flex: 1 0 150px;
            margin-right: 10px;
        }
        input[type="number"] {
            flex: 1 0 200px;
            padding: 5px;
        }
        .actions {
            text-align: center;
            margin-top: 10px;
        }
        .actions button {
            margin: 5px 5px;
            padding: 10px 20px;
        }
        /* Result and Error Messages */
        .result, .cooldown-message {
            margin-top: 20px;
            background-color: #e7ffe7;
            padding: 10px;
            border: 1px solid #b3ffb3;
            text-align: center;
        }
        .error {
            margin-top: 20px;
            background-color: #ffe7e7;
            padding: 10px;
            border: 1px solid #ffb3b3;
            text-align: center;
        }
        /* Checkbox Group */
        .checkbox-group {
            margin-bottom: 15px;
            display: flex;
            flex-wrap: wrap;
        }
        .checkbox-item {
            flex: 1 0 45%;
            box-sizing: border-box;
            margin-bottom: 5px;
        }
        /* Responsive Design */
        @media (max-width: 600px) {
            .form-group {
                flex-direction: column;
                align-items: stretch;
            }
            label, input[type="number"] {
                flex: 1 0 auto;
                margin: 0 0 5px 0;
            }
            .checkbox-item {
                flex: 1 0 100%;
            }
        }
        /* Loading Spinner */
        #loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        /* Footer Links */
        .footer-links {
            text-align: center;
            margin-top: 20px;
        }
        .footer-button {
            margin: 10px 5px;
            padding: 10px 20px;
            text-decoration: none;
            color: white;
            background-color: #007BFF;
            border: none;
            display: inline-block;
            cursor: pointer;
            font-size: 16px;
        }
        .footer-button:hover {
            background-color: #0056b3;
        }
        .made-by {
            margin-top: 10px;
        }
        .made-by a {
            text-decoration: none;
            color: blue;
            font-size: 16px;
        }
        .made-by a:hover {
            text-decoration: underline;
        }
        /* Select Location Button */
        .map-button {
            display: block;
            margin: 20px auto;
            padding: 15px 30px;
            font-size: 18px;
            background-color: #28a745;
            color: white;
            border: none;
            cursor: pointer;
        }
        .map-button:hover {
            background-color: #218838;
        }
        /* Spacing Between Check All/Uncheck All Buttons */
        .check-buttons {
            text-align: center;
            margin-bottom: 15px;
        }
        .check-buttons button {
            margin: 5px 10px;
            padding: 10px 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>OpenStreetMap Business Scraper</h1>
    <p>Fetch business data from OpenStreetMap based on location and categories.</p>
	<br><br><br>
    <form action="fetch_data.php" method="POST" id="businessForm">
        <!-- Latitude -->
        <div class="form-group">
            <label for="latitude">Latitude:</label>
            <input type="number" step="any" name="latitude" id="latitude" required value="<?php echo isset($_SESSION['latitude']) ? htmlspecialchars($_SESSION['latitude']) : ''; ?>">
        </div>
        <!-- Longitude -->
        <div class="form-group">
            <label for="longitude">Longitude:</label>
            <input type="number" step="any" name="longitude" id="longitude" required value="<?php echo isset($_SESSION['longitude']) ? htmlspecialchars($_SESSION['longitude']) : ''; ?>">
        </div>
        <!-- Radius -->
        <div class="form-group">
            <label for="radius">Radius (km):</label>
            <input type="number" step="any" min="0.1" max="9999" name="radius" id="radius" required value="<?php echo isset($_SESSION['radius']) ? htmlspecialchars($_SESSION['radius']) : ''; ?>">
        </div>
        <!-- Select Location on Map -->
        <div class="form-group">
            <button type="button" class="map-button" onclick="openMap()">Select Location on Map</button>
        </div>
        <!-- Exclude Entries Without Phone -->
        <div class="form-group">
            <label><input type="checkbox" name="exclude_no_phone" <?php echo isset($_SESSION['exclude_no_phone']) ? 'checked' : ''; ?>> Exclude entries without phone number</label>
        </div><br><br>
		<hr><br><br>
        <!-- Categories -->
        <div class="checkbox-group">
            <?php
            // Categories for selection
            $categories = [
                ['Shop', 'shop', 'null'],
                ['Office', 'office', 'null'],
                ['Restaurant', 'amenity', 'restaurant'],
                ['Cafe', 'amenity', 'cafe'],
                ['Bar', 'amenity', 'bar'],
                ['Pub', 'amenity', 'pub'],
                ['Fast Food', 'amenity', 'fast_food'],
                ['Bank', 'amenity', 'bank'],
                ['Pharmacy', 'amenity', 'pharmacy'],
                ['Hospital', 'amenity', 'hospital'],
                ['Clinic', 'amenity', 'clinic'],
                ['Dentist', 'amenity', 'dentist'],
                ['Doctors', 'amenity', 'doctors'],
                ['Theatre', 'amenity', 'theatre'],
                ['Cinema', 'amenity', 'cinema'],
                ['Nightclub', 'amenity', 'nightclub'],
                ['Kindergarten', 'amenity', 'kindergarten'],
                ['Library', 'amenity', 'library'],
                ['College', 'amenity', 'college'],
                ['University', 'amenity', 'university'],
                ['Parking', 'amenity', 'parking'],
                ['Fuel Station', 'amenity', 'fuel'],
                ['Hotel', 'tourism', 'hotel'],
                ['Motel', 'tourism', 'motel'],
                ['Guest House', 'tourism', 'guest_house'],
                ['Supermarket', 'shop', 'supermarket'],
                ['Convenience Store', 'shop', 'convenience'],
                ['Bakery', 'shop', 'bakery'],
                ['Butcher', 'shop', 'butcher'],
                ['Clothes Store', 'shop', 'clothes'],
                ['Electronics Store', 'shop', 'electronics'],
                ['Furniture Store', 'shop', 'furniture'],
                ['Jewelry Store', 'shop', 'jewelry'],
                ['Sports Shop', 'shop', 'sports'],
                ['Hairdresser', 'shop', 'hairdresser'],
                ['Beauty Salon', 'shop', 'beauty'],
                ['Museum', 'tourism', 'museum'],
                ['Park', 'leisure', 'park'],
                ['ATM', 'amenity', 'atm'],
                ['Post Office', 'amenity', 'post_office'],
                ['Police Station', 'amenity', 'police'],
                ['Fire Station', 'amenity', 'fire_station'],
                ['Embassy', 'amenity', 'embassy'],
                ['Court', 'amenity', 'courthouse'],
                ['Place of Worship', 'amenity', 'place_of_worship'],
                ['Veterinary Clinic', 'amenity', 'veterinary'],
                ['Swimming Pool', 'leisure', 'swimming_pool'],
                ['Gym', 'leisure', 'fitness_centre'],
                ['Playground', 'leisure', 'playground'],
                ['Bus Station', 'amenity', 'bus_station'],
                ['Train Station', 'railway', 'station'],
                ['Airport', 'aeroway', 'aerodrome'],
                ['Taxi Stand', 'amenity', 'taxi'],
                ['Car Rental', 'amenity', 'car_rental'],
                ['Car Wash', 'amenity', 'car_wash'],
                ['Charging Station', 'amenity', 'charging_station'],
                ['School', 'amenity', 'school'],
                ['Casino', 'amenity', 'casino'],
                ['Artwork', 'tourism', 'artwork'],
                ['Information', 'tourism', 'information'],
                ['Viewpoint', 'tourism', 'viewpoint'],
                ['Zoo', 'tourism', 'zoo'],
                ['Theme Park', 'tourism', 'theme_park'],
                ['Water Park', 'leisure', 'water_park'],
            ];

            foreach ($categories as $index => $category) {
                $displayName = $category[0];
                $tag = $category[1];
                $value = $category[2];
                $valueAttr = $value ? $value : 'null';
                $checked = 'checked';
                if (isset($_SESSION['selected_categories'])) {
                    $checked = in_array("$tag|$valueAttr", $_SESSION['selected_categories']) ? 'checked' : '';
                }
                echo "<div class='checkbox-item'><label><input type='checkbox' name='categories[]' value='{$tag}|{$valueAttr}' $checked> {$displayName}</label></div>";
            }
            ?>
        </div>
        <!-- Check All / Uncheck All -->
        <br><br><div class="check-buttons">
            <button type="button" onclick="checkAll()">Check All</button>
            <button type="button" onclick="uncheckAll()">Uncheck All</button>
        </div><br><hr>
		<!-- Actions -->
        <div class="actions">
			<br><br>
            <button type="submit" name="action" value="fetch">Fetch Businesses</button><br>
            <button type="submit" name="action" value="remove_duplicates">Remove Duplicate Names</button><br>
            <button type="submit" name="action" value="save">Save Data</button>
        </div>
    </form>

    <!-- Loading Indicator -->
    <div id="loading">
        <p>Loading... Please wait.</p>
    </div>

    <?php
    if (isset($_SESSION['message'])) {
        echo "<div class='result'>" . htmlspecialchars($_SESSION['message']) . "</div>";
    }
    if (isset($_SESSION['error'])) {
        echo "<div class='error'>" . htmlspecialchars($_SESSION['error']) . "</div>";
    }
    ?>
    <h2>Processed: <?php echo isset($_SESSION['processed_count']) ? htmlspecialchars($_SESSION['processed_count']) : '0'; ?></h2>

    <!-- Cooldown Message -->
    <?php if ($cooldown_seconds > 0): ?>
        <div class="cooldown-message">
            Please wait <span id="cooldown-timer"><?php echo $cooldown_seconds; ?></span> seconds before making another request.
        </div>
    <?php endif; ?>

    <!-- Footer Links -->
    <div class="footer-links">
        <a href="https://github.com/Eykthirnyr/OSM-Business-Scraper" target="_blank" class="footer-button">GitHub Repository</a>
        <div class="made-by">
            <a href="https://clement.business/" target="_blank">Made by Clément GHANEME</a>
        </div>
    </div>
</div>

<script>
function checkAll() {
    var checkboxes = document.querySelectorAll('input[name="categories[]"]');
    checkboxes.forEach((checkbox) => {
        checkbox.checked = true;
    });
}

function uncheckAll() {
    var checkboxes = document.querySelectorAll('input[name="categories[]"]');
    checkboxes.forEach((checkbox) => {
        checkbox.checked = false;
    });
}

function openMap() {
    window.open('map.html', 'Select Location', 'width=800,height=600');
}

// Show loading indicator on form submit
document.getElementById('businessForm').addEventListener('submit', function(event) {
    // Check if cooldown is active
    var cooldownSeconds = <?php echo isset($cooldown_seconds) ? $cooldown_seconds : 0; ?>;
    if (cooldownSeconds > 0 && event.submitter.name === 'action' && event.submitter.value === 'fetch') {
        alert('Please wait for the cooldown to finish before making another request.');
        event.preventDefault();
        return false;
    }
    document.getElementById('loading').style.display = 'block';
});

// Live Countdown Timer
var cooldownSeconds = <?php echo isset($cooldown_seconds) ? $cooldown_seconds : 0; ?>;
if (cooldownSeconds > 0) {
    var cooldownTimer = document.getElementById('cooldown-timer');
    var countdownInterval = setInterval(function() {
        cooldownSeconds--;
        cooldownTimer.textContent = cooldownSeconds;
        if (cooldownSeconds <= 0) {
            clearInterval(countdownInterval);
            // Reload the page to update the cooldown message
            window.location.reload();
        }
    }, 1000);
}
</script>

</body>
</html>
