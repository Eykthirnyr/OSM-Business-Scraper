<?php
// fetch_data.php
session_start();

require 'vendor/autoload.php'; // For PhpSpreadsheet

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;

// Initialize or retrieve results from session
if (!isset($_SESSION['all_results'])) {
    $_SESSION['all_results'] = [];
}

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $action = $_POST['action'];

    // Retain input data
    $_SESSION['latitude'] = $_POST['latitude'];
    $_SESSION['longitude'] = $_POST['longitude'];
    $_SESSION['radius'] = $_POST['radius'];
    $_SESSION['exclude_no_phone'] = isset($_POST['exclude_no_phone']) ? true : false;
    $_SESSION['selected_categories'] = isset($_POST['categories']) ? $_POST['categories'] : [];

    // Input validation
    if (!is_numeric($_SESSION['latitude']) || !is_numeric($_SESSION['longitude']) || !is_numeric($_SESSION['radius'])) {
        $_SESSION['error'] = 'Latitude, longitude, and radius must be numeric values.';
        header('Location: index.php');
        exit();
    }

    // Validate radius range
    if ($_SESSION['radius'] < 0.1 || $_SESSION['radius'] > 9999) {
        $_SESSION['error'] = 'Radius must be between 0.1 and 9999 kilometers.';
        header('Location: index.php');
        exit();
    }

    if ($action == 'fetch') {
        // Check for cooldown
        $ip_address = $_SERVER['REMOTE_ADDR'];
        $cooldown_file = 'cooldown.json';

        // Load cooldown data
        $cooldowns = [];
        if (file_exists($cooldown_file)) {
            $cooldowns = json_decode(file_get_contents($cooldown_file), true);
        }

        $current_time = time();
        if (isset($cooldowns[$ip_address]) && $cooldowns[$ip_address] > $current_time) {
            $remaining_time = $cooldowns[$ip_address] - $current_time;
            $_SESSION['cooldown'] = $cooldowns[$ip_address];
            $_SESSION['error'] = "Please wait $remaining_time seconds before making another request.";
            header('Location: index.php');
            exit();
        } else {
            // Set new cooldown time (1 minute)
            $cooldowns[$ip_address] = $current_time + 60;
            file_put_contents($cooldown_file, json_encode($cooldowns));
            $_SESSION['cooldown'] = $cooldowns[$ip_address];
        }

        // Log the request
        logRequest($ip_address, $_SESSION['latitude'], $_SESSION['longitude'], $_SESSION['radius']);

        // Fetch businesses
        fetchBusinesses();
    } elseif ($action == 'remove_duplicates') {
        // Remove duplicates
        removeDuplicates();
    } elseif ($action == 'save') {
        // Save data to Excel
        saveData();
    }
    header('Location: index.php');
    exit();
}

function fetchBusinesses() {
    $latitude = $_SESSION['latitude'];
    $longitude = $_SESSION['longitude'];
    $radius = $_SESSION['radius'];
    $exclude_no_phone = $_SESSION['exclude_no_phone'];
    $selected_categories = $_SESSION['selected_categories'];

    if (empty($selected_categories)) {
        $_SESSION['error'] = 'Please select at least one category.';
        return;
    }

    // Build Overpass API query
    $overpass_url = 'http://overpass-api.de/api/interpreter';

    // Group selected categories by tag
    $tag_values = [];
    foreach ($selected_categories as $cat) {
        list($tag, $value) = explode('|', $cat);
        $tag_values[$tag][] = $value === 'null' ? null : $value;
    }

    // Build query parts
    $query_parts = [];
    foreach ($tag_values as $tag => $values) {
        if (in_array(null, $values)) {
            // For tags without specific values
            $query_parts[] = "node(around:" . ($radius * 1000) . ",$latitude,$longitude)[\"name\"][\"$tag\"];";
            $query_parts[] = "way(around:" . ($radius * 1000) . ",$latitude,$longitude)[\"name\"][\"$tag\"];";
        } else {
            // For tags with specific values
            $regex = implode('|', $values);
            $query_parts[] = "node(around:" . ($radius * 1000) . ",$latitude,$longitude)[\"name\"][\"$tag\"~\"$regex\"];";
            $query_parts[] = "way(around:" . ($radius * 1000) . ",$latitude,$longitude)[\"name\"][\"$tag\"~\"$regex\"];";
        }
    }

    $overpass_query = "[out:json];(" . implode('', $query_parts) . ");out center;";

    // Fetch data
    $context = stream_context_create([
        'http' => ['timeout' => 300] // Increase timeout if needed
    ]);
    $response = @file_get_contents($overpass_url . '?data=' . urlencode($overpass_query), false, $context);
    if ($response === false) {
        $_SESSION['error'] = 'Error fetching data from Overpass API.';
        return;
    }
    $data = json_decode($response, true);

    $all_results = [];
    $processed_count = 0;

    if (!isset($data['elements'])) {
        $_SESSION['error'] = 'No data returned from Overpass API.';
        return;
    }

    foreach ($data['elements'] as $element) {
        $tags = isset($element['tags']) ? $element['tags'] : [];
        $name = isset($tags['name']) ? $tags['name'] : null;
        $address = constructAddress($tags);
        $phone = isset($tags['phone']) ? $tags['phone'] : null;

        // Determine whether to include this entry
        $include_entry = true;
        if ($exclude_no_phone && !$phone) {
            $include_entry = false;
        }

        if ($name && $include_entry) {
            $all_results[] = [
                'Name' => $name,
                'Address' => $address,
                'Phone' => $phone ? $phone : 'N/A'
            ];
            $processed_count++;
        }
    }

    $_SESSION['all_results'] = array_merge($_SESSION['all_results'], $all_results);
    $_SESSION['processed_count'] = isset($_SESSION['processed_count']) ? $_SESSION['processed_count'] + $processed_count : $processed_count;
    if ($processed_count > 0) {
        $_SESSION['message'] = "Data fetched successfully. Total businesses: {$_SESSION['processed_count']}";
    } else {
        $_SESSION['error'] = 'No businesses found with the specified criteria.';
    }
}

function removeDuplicates() {
    if (empty($_SESSION['all_results'])) {
        $_SESSION['error'] = 'No data to process. Please fetch businesses first.';
        return;
    }

    $unique_results = [];
    $seen_names = [];

    foreach ($_SESSION['all_results'] as $entry) {
        $name = $entry['Name'];
        if (!in_array($name, $seen_names)) {
            $seen_names[] = $name;
            $unique_results[] = $entry;
        }
    }

    $duplicates_removed = count($_SESSION['all_results']) - count($unique_results);
    $_SESSION['all_results'] = $unique_results;
    $_SESSION['processed_count'] = count($unique_results);

    $_SESSION['message'] = "$duplicates_removed duplicate entries removed.";
}

function saveData() {
    if (empty($_SESSION['all_results'])) {
        $_SESSION['error'] = 'No data to save. Please fetch businesses first.';
        return;
    }

    $spreadsheet = new Spreadsheet();
    $sheet = $spreadsheet->getActiveSheet();
    $sheet->setTitle('Businesses');

    // Define headers
    $headers = ['Name', 'Address', 'Phone'];
    $sheet->fromArray($headers, null, 'A1');

    // Bold headers
    $styleArray = [
        'font' => [
            'bold' => true,
        ],
    ];
    $sheet->getStyle('A1:C1')->applyFromArray($styleArray);

    // Add data
    $row = 2;
    foreach ($_SESSION['all_results'] as $entry) {
        $sheet->setCellValue('A' . $row, $entry['Name']);
        $sheet->setCellValue('B' . $row, $entry['Address']);
        $sheet->setCellValue('C' . $row, $entry['Phone']);
        $row++;
    }

    // Adjust column widths
    foreach (range('A', 'C') as $columnID) {
        $sheet->getColumnDimension($columnID)->setAutoSize(true);
    }

    // Generate filename with date and time
    $filename = 'Fetched_Businesses_' . date('Y-m-d_H-i-s') . '.xlsx';
    $filepath = sys_get_temp_dir() . DIRECTORY_SEPARATOR . $filename;

    // Save to file
    $writer = new Xlsx($spreadsheet);
    $writer->save($filepath);

    // Provide download
    header('Content-Description: File Transfer');
    header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    header('Content-Disposition: attachment; filename="' . basename($filename) . '"');
    header('Cache-Control: must-revalidate');
    header('Expires: 0');
    header('Content-Length: ' . filesize($filepath));
    readfile($filepath);

    // Delete file after download
    unlink($filepath);

    // Clear session data after download
    unset($_SESSION['all_results']);
    unset($_SESSION['processed_count']);
    exit();
}

function constructAddress($tags) {
    $address_parts = [];
    $keys = ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode', 'addr:country'];
    foreach ($keys as $key) {
        if (isset($tags[$key])) {
            $address_parts[] = $tags[$key];
        }
    }
    return !empty($address_parts) ? implode(', ', $address_parts) : 'N/A';
}

function logRequest($ip, $latitude, $longitude, $radius) {
    $log_entry = date('Y-m-d H:i:s') . " - IP: $ip, Latitude: $latitude, Longitude: $longitude, Radius: $radius km" . PHP_EOL;
    file_put_contents('requests.log', $log_entry, FILE_APPEND | LOCK_EX);
}
