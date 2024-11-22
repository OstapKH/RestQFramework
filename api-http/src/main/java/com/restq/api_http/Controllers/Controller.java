package com.restq.api_http.Controllers;

import com.restq.api_http.DTO.*;
import com.restq.api_http.Repositories.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.sql.Date;
import java.time.LocalDate;
import java.util.List;
import java.util.Random;

@RestController
@RequestMapping("/api/reports")
public class Controller {

    @Autowired
    private LineItemRepository lineItemRepository;
    @Autowired
    private PartRepository supplierPartRepository;
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private SupplierRepository supplierRepository;
    @Autowired
    private NationRepository nationRepository;

    // Q1
    // This endpoint accepts DELTA and endDate as query parameters
    @GetMapping("/pricing-summary")
    public List<PricingSummaryReport> getPricingSummary(
            @RequestParam(value = "delta", defaultValue = "1") int delta,
            @RequestParam(value = "shipDate", defaultValue = "1998-12-01") Date shipDate
    ) {
        // If DELTA is not passed, generate a random DELTA between 60 and 120
        if (delta == 0 || delta > 120) {
            Random random = new Random();
            delta = 60 + random.nextInt(61);
        }

        // Calculate the endDate by adding DELTA days to the shipDate
        Date endDate = new Date(shipDate.getTime() + delta * 24 * 60 * 60 * 1000L);

        return lineItemRepository.getPricingSummaryReport(endDate);
    }

    // Q2
    @GetMapping("/supplier-part-info")
    public List<SupplierPartInfo> getSupplierPartInfo(
            @RequestParam(value = "size") Integer size,
            @RequestParam(value = "type") String type,
            @RequestParam(value = "region") String region) {
        return supplierPartRepository.findSupplierPartInfo(size, type, region);
    }

    // Q3
    @GetMapping("/order-revenue-info")
    public List<OrderRevenueInfo> getOrderRevenueInfo(
            @RequestParam(value = "segment") String segment,
            @RequestParam(value = "date") LocalDate date) {
        return orderRepository.findTopUnshippedOrders(segment, date);
    }

    // Q4
    @GetMapping("/order-priority-count")
    public List<OrderPriorityCountInfo> getOrderPriorityCount(
            @RequestParam(value = "date") LocalDate date) {
        LocalDate datePlus = date.plusMonths(3);
        return orderRepository.findOrderPriorityCount(date, datePlus);
    }

    // Q5
    @GetMapping("/local-supplier-volume")
    public List<LocalSupplierVolume> getLocalSupplierVolume(
            @RequestParam(value = "region") String region,
            @RequestParam(value = "startDate") LocalDate startDate) {
        LocalDate endDate = startDate.plusYears(1);
        return supplierRepository.findLocalSupplierVolume(region, startDate, endDate);
    }

    // Q6
    @GetMapping("/revenue-increase")
    public BigDecimal getRevenueIncrease(
            @RequestParam(value = "discount") Double discount,
            @RequestParam(value = "quantity") Integer quantity,
            @RequestParam(value = "startDate") Date startDate
    ) {
        Date endDate = Date.valueOf(startDate.toLocalDate().plusYears(1));
        return lineItemRepository.calculateRevenueIncrease(startDate, endDate, discount, quantity);
    }

    // Q7 (Modified)
    @GetMapping("/nations-volume-shipping")
    public List<VolumeShippingOfNations> getNationsVolumeShipping(
            @RequestParam(value = "nation1") String nation1,
            @RequestParam(value = "nation2") String nation2,
            @RequestParam(value = "startDate", defaultValue = "1995-01-01") Date startDate,
            @RequestParam(value = "endDate", defaultValue = "1995-12-31") Date endDate) {
        return nationRepository.getNationsVolumeShipping(nation1, nation2, startDate, endDate);
    }
}
